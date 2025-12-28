"""
OpenAI Service Wrapper for GPT-4o-mini
Provides a centralized interface for all LLM interactions
"""
import os
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI, OpenAIError, RateLimitError, APITimeoutError
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Wrapper for OpenAI API using GPT-4o-mini model
    Handles all LLM interactions with proper error handling and rate limiting
    """
    
    MODEL = "gpt-4o-mini"
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 1000
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI service
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"OpenAI service initialized with model: {self.MODEL}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Get chat completion from GPT-4o-mini
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            response_format: Optional format specification (e.g., {"type": "json_object"})
        
        Returns:
            Response content as string
        
        Raises:
            OpenAIError: If API call fails
        """
        try:
            # Log the input prompt
            print("\n" + "=" * 80)
            print("🤖 LLM INPUT PROMPT")
            print("=" * 80)
            for msg in messages:
                role = msg['role'].upper()
                content = msg['content']
                print(f"\n[{role}]:")
                print("-" * 80)
                print(content)
                print("-" * 80)
            
            kwargs = {
                "model": self.MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            # Log the output response
            print("\n" + "=" * 80)
            print("🤖 LLM OUTPUT RESPONSE")
            print("=" * 80)
            print(content)
            print("=" * 80 + "\n")
            
            logger.debug(f"OpenAI response received: {len(content)} characters")
            
            return content
        
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise OpenAIError("Rate limit exceeded. Please try again later.")
        
        except APITimeoutError as e:
            logger.error(f"OpenAI API timeout: {e}")
            raise OpenAIError("Request timed out. Please try again.")
        
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI service: {e}")
            raise OpenAIError(f"Failed to get completion: {str(e)}")
    
    def chat_completion_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ) -> Dict[str, Any]:
        """
        Get chat completion with JSON response format
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
        
        Returns:
            Parsed JSON response as dictionary
        
        Raises:
            OpenAIError: If API call fails
            json.JSONDecodeError: If response is not valid JSON
        """
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")
    
    def create_prompt(
        self,
        system_message: str,
        user_message: str
    ) -> List[Dict[str, str]]:
        """
        Create a messages list for chat completion
        
        Args:
            system_message: System prompt defining behavior
            user_message: User's input/question
        
        Returns:
            List of message dicts ready for chat_completion
        """
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    
    def test_connection(self) -> bool:
        """
        Test OpenAI API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.chat_completion(
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=10
            )
            logger.info("OpenAI connection test successful")
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False
