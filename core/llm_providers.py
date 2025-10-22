# core/llm_providers.py
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class GroqProvider:
    """Groq LLM Provider - FREE with high limits"""
    
    def __init__(self):
        self.available = self.check_availability()
    
    def check_availability(self) -> bool:
        return bool(GROQ_API_KEY)
    
    def chat_completion(self, messages: list, **kwargs) -> str:
        if not self.available:
            raise Exception("Groq API key not available")
        
        try:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Current free model
                messages=messages,
                temperature=kwargs.get("temperature", 0),
                max_tokens=kwargs.get("max_tokens", 1000)
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Groq API error: {e}")

# Global Groq provider instance
groq_provider = GroqProvider()

def have_llm() -> bool:
    """Check if Groq provider is available"""
    return groq_provider.available

def llm_chat(messages: list, **kwargs) -> str:
    """Make a chat completion using Groq"""
    if not have_llm():
        raise Exception("Groq provider not available")
    return groq_provider.chat_completion(messages, **kwargs)