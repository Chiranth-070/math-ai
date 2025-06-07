import logging
from pydantic import BaseModel
from typing import List
from agents import (
    Agent, 
    Runner, 
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
    output_guardrail,
)

logger = logging.getLogger(__name__)

# Simplified Input Guardrail Models
class MathInputValidationGuardrail(BaseModel):
    is_math_related: bool
    is_appropriate: bool
    reasoning: str

# Simplified Output Guardrail Models  
class MathOutputValidationGuardrail(BaseModel):
    is_math_related: bool
    is_appropriate: bool
    reasoning: str

# Enhanced Math Expert Response Model
class MathExpertResponse(BaseModel):
    session_id: str
    problem_analysis: str
    concept_explanation: str
    step_by_step_solution: str
    alternative_methods: List[str]
    key_formulas_used: List[str]
    common_mistakes_to_avoid: List[str]
    related_jee_topics: List[str]
    difficulty_level: str
    time_to_solve_minutes: int
    practice_recommendations: str
    memory_insights: str
    personalized_tips: str

# Math Input Guardrail Agent
math_input_guardrail_agent = Agent(
    name="Math Input Validator",
    instructions="""
    You are a mathematics input validator.
    
    Check if the query is:
    1. Related to mathematics (any level from basic to advanced)
    2. An appropriate educational question
    
    ACCEPT: 
    - All math topics (algebra, calculus, geometry, statistics, etc.)
    - Concept explanations and clarifications
    - Problem-solving questions
    - Solution methods and approaches
    - Math theory questions
    
    REJECT: 
    - Non-math topics
    - Inappropriate content
    - Off-topic queries
    
    Keep validation simple and focused.
    """,
    model="gpt-4.1-mini",
    output_type=MathInputValidationGuardrail,
)

# Math Output Guardrail Agent
math_output_guardrail_agent = Agent(
    name="Mathematics Output Validator", 
    instructions="""
    You are a very lenient output validator for mathematics responses.
    
    ACCEPT almost all responses unless they are completely inappropriate or empty.
    Only REJECT if:
    - Response is completely empty or gibberish
    - Response is completely unrelated to mathematics
    - Contains no actual mathematical content
    
    Be very generous and forgiving. Focus only on basic structure validation.
    Ensure responses contain some mathematical explanation, formulas, or problem-solving steps.
    """,
    model="gpt-4.1-mini",
    output_type=MathOutputValidationGuardrail,
)

@input_guardrail
async def math_input_guardrail_simple(
    ctx: RunContextWrapper[None], 
    agent: Agent, 
    input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    """Simplified input guardrail"""
    try:
        logger.info("Running math input validation...")
        
        if isinstance(input, list):
            input_text = str(input)
        else:
            input_text = input
            
        result = await Runner.run(math_input_guardrail_agent, input_text, context=ctx.context)
        validation_result = result.final_output
        
        should_trip = not (validation_result.is_math_related and validation_result.is_appropriate)
        
        if should_trip:
            logger.warning(f"Input rejected: {validation_result.reasoning}")
        else:
            logger.info("Input validation passed")
            
        return GuardrailFunctionOutput(
            output_info=validation_result,
            tripwire_triggered=should_trip,
        )
    except Exception as e:
        logger.error(f"Input guardrail error: {e}")
        return GuardrailFunctionOutput(
            output_info={"error": str(e)},
            tripwire_triggered=False,
        )
    
@output_guardrail  
async def math_output_guardrail_simple(
    ctx: RunContextWrapper, 
    agent: Agent, 
    output: MathExpertResponse
) -> GuardrailFunctionOutput:
    """Simplified output guardrail"""
    try:
        logger.info("Running math output validation...")
        
        output_summary = f"""
        Analysis: {output.problem_analysis[:200]}
        Solution: {output.step_by_step_solution[:200]}
        Concepts: {output.concept_explanation[:200]}
        """
        
        result = await Runner.run(math_output_guardrail_agent, output_summary, context=ctx.context)
        validation_result = result.final_output
        
        # Very lenient - only trip if explicitly marked as both non-math-related AND inappropriate
        should_trip = not (validation_result.is_math_related and validation_result.is_appropriate)
        
        if should_trip:
            logger.warning(f"Output rejected: {validation_result.reasoning}")
        else:
            logger.info("Output validation passed")
            
        return GuardrailFunctionOutput(
            output_info=validation_result,
            tripwire_triggered=should_trip,
        )
        
    except Exception as e:
        logger.error(f"Output guardrail error: {e}")
        return GuardrailFunctionOutput(
            output_info={"error": str(e)},
            tripwire_triggered=False,
        )