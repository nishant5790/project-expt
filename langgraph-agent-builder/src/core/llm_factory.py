"""Factory for creating LLM instances based on provider configuration."""

import os
from typing import Any, Dict, Optional
from ..config import LLMProvider

# Import LangChain components with fallbacks
try:
    from langchain_openai import ChatOpenAI, AzureChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain_core.language_models import BaseChatModel
except ImportError:
    # Fallback LLM implementations
    class BaseChatModel:
        def __init__(self, **kwargs):
            self.model = kwargs.get('model', 'mock-model')
            self.temperature = kwargs.get('temperature', 0.7)
            
        def invoke(self, messages):
            # Mock response
            if isinstance(messages, list) and messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    content = last_message.content
                else:
                    content = str(last_message)
                return MockAIMessage(f"Mock response to: {content}")
            return MockAIMessage("Mock response")
    
    class ChatOpenAI(BaseChatModel):
        pass
    
    class AzureChatOpenAI(BaseChatModel):
        pass
    
    class ChatAnthropic(BaseChatModel):
        pass

# Mock message class
class MockAIMessage:
    def __init__(self, content):
        self.content = content


class LLMFactory:
    """Factory for creating LLM instances."""
    
    @staticmethod
    def create_llm(
        provider: LLMProvider,
        model: str,
        api_key_env: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> BaseChatModel:
        """
        Create an LLM instance based on provider.
        
        Args:
            provider: The LLM provider
            model: Model name
            api_key_env: Environment variable for API key
            temperature: Temperature for sampling
            max_tokens: Maximum tokens for response
            **kwargs: Additional provider-specific arguments
            
        Returns:
            A configured LLM instance
        """
        # Get API key from environment
        api_key = None
        if api_key_env:
            api_key = os.getenv(api_key_env)
            if not api_key:
                raise ValueError(f"API key not found in environment variable: {api_key_env}")
        
        # Create LLM based on provider
        if provider == LLMProvider.OPENAI:
            return LLMFactory._create_openai_llm(model, api_key, temperature, max_tokens, **kwargs)
        elif provider == LLMProvider.ANTHROPIC:
            return LLMFactory._create_anthropic_llm(model, api_key, temperature, max_tokens, **kwargs)
        elif provider == LLMProvider.AZURE_OPENAI:
            return LLMFactory._create_azure_openai_llm(model, api_key, temperature, max_tokens, **kwargs)
        elif provider == LLMProvider.BEDROCK:
            return LLMFactory._create_bedrock_llm(model, temperature, max_tokens, **kwargs)
        elif provider == LLMProvider.CUSTOM:
            return LLMFactory._create_custom_llm(model, api_key, temperature, max_tokens, **kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def _create_openai_llm(
        model: str,
        api_key: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> ChatOpenAI:
        """Create OpenAI LLM."""
        params = {
            "model": model,
            "temperature": temperature,
        }
        
        if api_key:
            params["openai_api_key"] = api_key
        if max_tokens:
            params["max_tokens"] = max_tokens
            
        # Add any additional kwargs
        params.update(kwargs)
        
        return ChatOpenAI(**params)
    
    @staticmethod
    def _create_anthropic_llm(
        model: str,
        api_key: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> ChatAnthropic:
        """Create Anthropic LLM."""
        params = {
            "model": model,
            "temperature": temperature,
        }
        
        if api_key:
            params["anthropic_api_key"] = api_key
        if max_tokens:
            params["max_output_tokens"] = max_tokens
            
        # Add any additional kwargs
        params.update(kwargs)
        
        return ChatAnthropic(**params)
    
    @staticmethod
    def _create_azure_openai_llm(
        model: str,
        api_key: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> AzureChatOpenAI:
        """Create Azure OpenAI LLM."""
        # Azure requires additional configuration
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", model)
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
        
        params = {
            "azure_deployment": azure_deployment,
            "temperature": temperature,
            "api_version": api_version,
        }
        
        if api_key:
            params["openai_api_key"] = api_key
        if azure_endpoint:
            params["azure_endpoint"] = azure_endpoint
        if max_tokens:
            params["max_tokens"] = max_tokens
            
        # Add any additional kwargs
        params.update(kwargs)
        
        return AzureChatOpenAI(**params)
    
    @staticmethod
    def _create_bedrock_llm(
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> BaseChatModel:
        """Create Bedrock LLM."""
        # This would require bedrock-specific implementation
        raise NotImplementedError("Bedrock LLM support not yet implemented")
    
    @staticmethod
    def _create_custom_llm(
        model: str,
        api_key: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> BaseChatModel:
        """Create custom LLM."""
        # This would load a custom LLM class
        custom_class_name = kwargs.get("custom_class")
        if not custom_class_name:
            raise ValueError("custom_class must be specified for CUSTOM provider")
        
        # Dynamic import of custom class
        # This is a placeholder - actual implementation would need proper module loading
        raise NotImplementedError("Custom LLM support requires implementation")


class LLMManager:
    """Manages LLM instances and configurations."""
    
    def __init__(self, default_config: Dict[str, Any]):
        """Initialize LLM manager."""
        self.default_config = default_config
        self._llm_cache: Dict[str, BaseChatModel] = {}
        
    def get_llm(
        self,
        node_config: Optional[Dict[str, Any]] = None,
        cache_key: Optional[str] = None
    ) -> BaseChatModel:
        """
        Get an LLM instance, using cache if available.
        
        Args:
            node_config: Node-specific LLM configuration
            cache_key: Key for caching the LLM instance
            
        Returns:
            An LLM instance
        """
        # Merge configurations
        config = self.default_config.copy()
        if node_config:
            config.update(node_config)
        
        # Check cache
        if cache_key and cache_key in self._llm_cache:
            return self._llm_cache[cache_key]
        
        # Create new LLM
        llm = LLMFactory.create_llm(**config)
        
        # Cache if requested
        if cache_key:
            self._llm_cache[cache_key] = llm
            
        return llm
    
    def clear_cache(self) -> None:
        """Clear LLM cache."""
        self._llm_cache.clear() 