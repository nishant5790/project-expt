"""Example: Using YAML configuration with custom tools via API"""

import httpx
import yaml
import asyncio
from pathlib import Path


async def main():
    """Demonstrate YAML configuration and custom tools."""
    base_url = "http://localhost:8000"
    
    print("=== LangGraph Agent Builder: YAML + Custom Tools Demo ===\n")
    
    # Step 1: Register custom tools
    print("Step 1: Registering custom tools...")
    
    # Custom tool 1: Text analyzer
    text_analyzer_tool = {
        "name": "text_analyzer",
        "description": "Analyze text for word count, sentiment, and key information",
        "function_code": '''
def analyze_text(text: str, analysis_type: str = "basic") -> str:
    """Analyze text content."""
    import re
    
    word_count = len(text.split())
    char_count = len(text)
    sentence_count = len(re.split(r'[.!?]+', text)) - 1
    
    if analysis_type == "basic":
        return f"Word count: {word_count}, Characters: {char_count}, Sentences: {sentence_count}"
    elif analysis_type == "keywords":
        # Simple keyword extraction
        words = re.findall(r'\\b\\w+\\b', text.lower())
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Only consider words longer than 3 chars
                word_freq[word] = word_freq.get(word, 0) + 1
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return f"Top keywords: {[word for word, freq in top_words]}"
    else:
        return f"Analysis type '{analysis_type}' not supported"
''',
        "parameters_schema": {
            "text": {
                "type": "string",
                "description": "The text to analyze"
            },
            "analysis_type": {
                "type": "string", 
                "description": "Type of analysis: 'basic' or 'keywords'",
                "default": "basic"
            }
        }
    }
    
    # Custom tool 2: Simple translator
    translator_tool = {
        "name": "simple_translator",
        "description": "Simple text translator (mock implementation)",
        "function_code": '''
def translate_text(text: str, target_language: str = "spanish") -> str:
    """Translate text to target language (mock implementation)."""
    
    # Mock translations for demo
    translations = {
        "spanish": {
            "hello": "hola",
            "goodbye": "adiós", 
            "thank you": "gracias",
            "please": "por favor",
            "yes": "sí",
            "no": "no"
        },
        "french": {
            "hello": "bonjour",
            "goodbye": "au revoir",
            "thank you": "merci",
            "please": "s'il vous plaît", 
            "yes": "oui",
            "no": "non"
        }
    }
    
    text_lower = text.lower()
    if target_language in translations:
        for english, translated in translations[target_language].items():
            text_lower = text_lower.replace(english, translated)
        return f"Translated to {target_language}: {text_lower}"
    else:
        return f"Translation to {target_language} not available (mock translator)"
''',
        "parameters_schema": {
            "text": {
                "type": "string",
                "description": "Text to translate"
            },
            "target_language": {
                "type": "string",
                "description": "Target language: 'spanish' or 'french'",
                "default": "spanish"
            }
        }
    }
    
    # Register the custom tools
    async with httpx.AsyncClient() as client:
        try:
            # Register text analyzer
            response = await client.post(f"{base_url}/tools/custom", json=text_analyzer_tool)
            if response.status_code == 200:
                print("✅ Text analyzer tool registered")
            else:
                print(f"❌ Failed to register text analyzer: {response.text}")
                
            # Register translator
            response = await client.post(f"{base_url}/tools/custom", json=translator_tool)
            if response.status_code == 200:
                print("✅ Translator tool registered")
            else:
                print(f"❌ Failed to register translator: {response.text}")
                
        except Exception as e:
            print(f"❌ Error registering tools: {e}")
            return
    
    # Step 2: Create YAML configuration
    print("\nStep 2: Creating YAML configuration...")
    
    yaml_config = {
        "name": "text-processing-agent",
        "description": "An agent that processes and analyzes text using custom tools",
        "version": "1.0.0",
        "llm_provider": "openai",
        "model": "gpt-3.5-turbo", 
        "api_key_env": "OPENAI_API_KEY",
        "temperature": 0.7,
        "workflow_type": "conditional",
        "tools": [
            "text_analyzer",
            "simple_translator",
            "calculator"
        ],
        "nodes": [
            {
                "name": "classify_task",
                "type": "llm",
                "description": "Classify the text processing task",
                "prompt": '''Classify this text processing request into one of these categories:
- "analyze": Text analysis (word count, keywords, etc.)
- "translate": Text translation
- "calculate": Mathematical calculation
- "general": General text processing

Respond with only the category name.'''
            },
            {
                "name": "route_task",
                "type": "conditional",
                "description": "Route to appropriate processor",
                "condition": "state['output'].strip().lower()",
                "branches": {
                    "analyze": "analyze_text",
                    "translate": "translate_text", 
                    "calculate": "do_calculation",
                    "default": "general_processing"
                }
            },
            {
                "name": "analyze_text",
                "type": "tool",
                "description": "Analyze text content",
                "tool": "text_analyzer",
                "tool_config": {
                    "text": "$input",
                    "analysis_type": "basic"
                }
            },
            {
                "name": "translate_text",
                "type": "tool", 
                "description": "Translate text",
                "tool": "simple_translator",
                "tool_config": {
                    "text": "$input",
                    "target_language": "spanish"
                }
            },
            {
                "name": "do_calculation", 
                "type": "tool",
                "description": "Perform calculation",
                "tool": "calculator",
                "tool_config": {
                    "expression": "$input"
                }
            },
            {
                "name": "general_processing",
                "type": "llm",
                "description": "General text processing",
                "prompt": "Process this text request and provide a helpful response."
            },
            {
                "name": "format_results",
                "type": "llm", 
                "description": "Format the final results",
                "prompt": '''Format the results from the previous processing step into a clear, user-friendly response.
Include:
1. What was processed
2. The results or output
3. Any additional insights or suggestions'''
            }
        ],
        "edges": [
            {"source": "classify_task", "target": "route_task"},
            {"source": "analyze_text", "target": "format_results"},
            {"source": "translate_text", "target": "format_results"},
            {"source": "do_calculation", "target": "format_results"},
            {"source": "general_processing", "target": "format_results"}
        ],
        "entry_point": "classify_task",
        "timeout": 300,
        "enable_logging": True,
        "enable_metrics": True
    }
    
    # Save YAML to file
    yaml_file = Path("text_processing_agent.yaml")
    with open(yaml_file, 'w') as f:
        yaml.dump(yaml_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ YAML configuration saved to {yaml_file}")
    
    # Step 3: Create agent from YAML
    print("\nStep 3: Creating agent from YAML...")
    
    async with httpx.AsyncClient() as client:
        try:
            with open(yaml_file, 'rb') as f:
                files = {"file": ("text_processing_agent.yaml", f, "application/x-yaml")}
                response = await client.post(f"{base_url}/agents/from-yaml", files=files)
                
            if response.status_code == 200:
                result = response.json()
                agent_name = result["agent_name"]
                print(f"✅ Agent created: {agent_name}")
            else:
                print(f"❌ Failed to create agent: {response.text}")
                return
                
        except Exception as e:
            print(f"❌ Error creating agent: {e}")
            return
    
    # Step 4: Test the agent with different inputs
    print("\nStep 4: Testing the agent...")
    
    test_cases = [
        {
            "description": "Text analysis request",
            "input": "This is a sample text for analysis. It contains multiple sentences and various words that we can analyze for patterns."
        },
        {
            "description": "Translation request",
            "input": "hello goodbye thank you please"
        },
        {
            "description": "Calculation request", 
            "input": "25 * 4 + 10"
        },
        {
            "description": "General request",
            "input": "Can you help me understand what this agent can do?"
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_case['description']}")
            print(f"Input: {test_case['input']}")
            
            try:
                response = await client.post(
                    f"{base_url}/agents/{agent_name}/invoke",
                    json={
                        "input": {"input": test_case['input']},
                        "metadata": {"test_case": i}
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Output: {result.get('output', 'No output')}")
                else:
                    print(f"❌ Error: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error invoking agent: {e}")
    
    # Step 5: Show available tools
    print("\nStep 5: Listing all available tools...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/tools")
            if response.status_code == 200:
                tools = response.json()["tools"]
                print(f"Available tools ({len(tools)}):")
                for tool_name, description in tools.items():
                    print(f"  - {tool_name}: {description}")
            else:
                print(f"❌ Error listing tools: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Cleanup
    yaml_file.unlink()  # Remove the temporary YAML file
    print(f"\n✅ Demo completed! Cleaned up {yaml_file}")


if __name__ == "__main__":
    print("Note: Make sure the API server is running (python -m src.main)")
    print("Also ensure you have OPENAI_API_KEY set in your environment\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}") 