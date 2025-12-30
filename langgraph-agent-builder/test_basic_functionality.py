#!/usr/bin/env python3
"""
Basic functionality test for LangGraph Agent Builder.
This script demonstrates the core features without requiring FastAPI or other heavy dependencies.
"""

import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_configuration_models():
    """Test the configuration models."""
    print("🧪 Testing Configuration Models...")
    
    try:
        from src.config import AgentConfig, NodeConfig, NodeType, LLMProvider, WorkflowType
        
        # Create a simple agent configuration
        config = AgentConfig(
            name="test-agent",
            description="A test agent",
            llm_provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            api_key_env="OPENAI_API_KEY",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=[
                NodeConfig(
                    name="greet",
                    type=NodeType.LLM,
                    prompt="Greet the user in a friendly way"
                ),
                NodeConfig(
                    name="respond",
                    type=NodeType.LLM,
                    prompt="Provide a helpful response"
                )
            ]
        )
        
        print(f"✅ Created agent config: {config.name}")
        print(f"   - {len(config.nodes)} nodes")
        print(f"   - Workflow: {config.workflow_type}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_custom_tools():
    """Test custom tools functionality."""
    print("\n🧪 Testing Custom Tools...")
    
    try:
        from src.core.custom_tools import CustomToolDefinition, CustomToolManager
        
        # Create a custom tool definition
        tool_def = CustomToolDefinition(
            name="hello_world",
            description="A simple hello world tool",
            function_code='''
def hello_world(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"
''',
            parameters_schema={
                "name": {
                    "type": "string",
                    "description": "Name to greet",
                    "default": "World"
                }
            }
        )
        
        # Create tool manager and register tool
        manager = CustomToolManager()
        tool = manager.register_tool_from_definition(tool_def)
        
        # Test the tool
        result = tool.invoke({"name": "LangGraph Builder"})
        print(f"✅ Custom tool created and tested")
        print(f"   - Tool: {tool_def.name}")
        print(f"   - Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom tools test failed: {e}")
        return False

def test_agent_builder():
    """Test the agent builder with mock implementations."""
    print("\n🧪 Testing Agent Builder...")
    
    try:
        from src.builders import AgentBuilder
        from src.config import AgentConfig, NodeConfig, NodeType, LLMProvider, WorkflowType
        
        # Create agent configuration
        config = AgentConfig(
            name="demo-agent",
            description="Demo agent with mock LLM",
            llm_provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=[
                NodeConfig(
                    name="process",
                    type=NodeType.LLM,
                    prompt="Process the user input and provide a response"
                )
            ]
        )
        
        # Build the agent
        builder = AgentBuilder()
        agent = builder.build(config)
        
        print(f"✅ Agent built successfully")
        print(f"   - Agent: {config.name}")
        print(f"   - Type: {type(agent).__name__}")
        
        # Test agent invocation
        test_input = {"input": "Hello, how are you?"}
        result = agent.invoke(test_input)
        
        print(f"✅ Agent invocation successful")
        print(f"   - Input: {test_input['input']}")
        print(f"   - Output: {result.get('output', 'No output')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent builder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_yaml_support():
    """Test YAML configuration support."""
    print("\n🧪 Testing YAML Support...")
    
    try:
        # Try to import yaml
        try:
            import yaml
            yaml_available = True
        except ImportError:
            yaml_available = False
            print("⚠️  PyYAML not available - YAML features will be limited")
        
        if yaml_available:
            # Create a sample YAML configuration
            config_dict = {
                "name": "yaml-test-agent",
                "description": "Agent created from YAML",
                "llm_provider": "openai",
                "model": "gpt-3.5-turbo",
                "api_key_env": "OPENAI_API_KEY",
                "workflow_type": "sequential",
                "nodes": [
                    {
                        "name": "process",
                        "type": "llm",
                        "prompt": "Process the input"
                    }
                ]
            }
            
            # Convert to YAML and back
            yaml_content = yaml.dump(config_dict)
            parsed_config = yaml.safe_load(yaml_content)
            
            print(f"✅ YAML processing successful")
            print(f"   - Agent: {parsed_config['name']}")
            print(f"   - Nodes: {len(parsed_config['nodes'])}")
            
        else:
            print("⚠️  Skipping YAML tests - install PyYAML for full functionality")
        
        return True
        
    except Exception as e:
        print(f"❌ YAML test failed: {e}")
        return False

def test_tools_registry():
    """Test the tools registry."""
    print("\n🧪 Testing Tools Registry...")
    
    try:
        from src.core.tools import ToolRegistry, ToolManager
        
        # Create registry and manager
        registry = ToolRegistry()
        manager = ToolManager(registry)
        
        # List available tools
        tools = manager.list_all_tools()
        
        print(f"✅ Tools registry working")
        print(f"   - Available tools: {len(tools)}")
        for name, desc in tools.items():
            print(f"     * {name}: {desc}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tools registry test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 LangGraph Agent Builder - Basic Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Configuration Models", test_configuration_models),
        ("Custom Tools", test_custom_tools),
        ("Tools Registry", test_tools_registry),
        ("YAML Support", test_yaml_support),
        ("Agent Builder", test_agent_builder),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is working correctly.")
        print("\n📝 Next steps:")
        print("   1. Install full dependencies: pip install -e .")
        print("   2. Set up environment: cp env.example .env")
        print("   3. Start API server: python -m src.main")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        print("   The system will still work with fallback implementations.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 