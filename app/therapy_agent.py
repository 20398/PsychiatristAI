import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os

# Initialize models
# We use a lower temperature for classification tasks, and slightly higher for creative, empathetic generation.
classifier_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
generator_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.6)

# Data structure for the Emotion Classifier
class EmotionClassification(BaseModel):
    primary_emotion: str = Field(description="e.g., anxiety, sadness, anger, overwhelmed")
    intensity: int = Field(description="1-10 intensity level of the emotion")
    intent: str = Field(description="e.g., venting, seeking advice, seeking validation, lost")
    crisis_risk_level: str = Field(description="None, Low, Medium, High. Explicitly check for self-harm or hopelessness.")

# 1. Emotion & Intent Classifier Prompt
classifier_prompt = ChatPromptTemplate.from_messages([
    ("system", "Analyze the following user input and determine emotional state, intent, and crisis risk. Be highly sensitive to safety issues."),
    ("human", "{user_input}")
])

# 2. Strategy Selector Prompt
strategy_prompt = ChatPromptTemplate.from_messages([
    ("system", """Given the user's emotional state: {emotion}, intent: {intent}, and current conversation stage: {stage}.
Select the most appropriate conversational strategy from this exact list:
[reflect, probe, reassure, reframe, suggest, ground]
Return ONLY the exact strategy name as a single word.""")
])

# 3. Response Generator Prompt
response_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an empathetic, professional AI conversational agent providing therapeutic-style support. 
Rules:
1. NEVER jump to offering solutions immediately. Focus on understanding and validating the emotion first.
2. Ask only ONE question per response.
3. Be non-judgmental, warm, concise, and highly human-like.
4. Apply the selected conversational strategy: {strategy}.
5. Do NOT sound robotic. Stay conversational.

Context:
User Emotion: {emotion} (Intensity: {intensity}/10)
Conversation Stage: {stage}
Recent Memory Context (if any): {short_term_memory}
"""),
    ("human", "{user_input}")
])

# Pipeline Methods

async def classify_message(user_input: str) -> EmotionClassification:
    """Extracts the emotion, intensity, and crisis level from the user's input."""
    chain = classifier_prompt | classifier_llm.with_structured_output(EmotionClassification)
    return await chain.ainvoke({"user_input": user_input})

async def select_strategy(emotion: str, intent: str, stage: str) -> str:
    """Selects the therapeutic conversational strategy based on the current state."""
    chain = strategy_prompt | classifier_llm
    result = await chain.ainvoke({"emotion": emotion, "intent": intent, "stage": stage})
    return result.content.strip().lower()

async def generate_response(
    user_input: str, 
    classification: EmotionClassification, 
    stage: str, 
    strategy: str, 
    short_term_memory: str = "No prior context."
) -> str:
    """Generates the final conversational response, checking for crisis first."""
    
    # Crisis Handler Interception
    if classification.crisis_risk_level in ["Medium", "High"]:
        return ("I'm hearing how much pain you're in right now, and I want to make sure you're safe. "
                "You don't have to carry this alone. Please reach out to someone who can help immediately, "
                "like the Suicide & Crisis Lifeline by dialing 988, or text HOME to 741741 to connect with a counselor.")

    # Normal Generation
    chain = response_prompt | generator_llm
    result = await chain.ainvoke({
        "strategy": strategy,
        "emotion": classification.primary_emotion,
        "intensity": classification.intensity,
        "stage": stage,
        "short_term_memory": short_term_memory,
        "user_input": user_input
    })
    
    return result.content
