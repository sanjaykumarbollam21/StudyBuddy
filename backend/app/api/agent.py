from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.agent import AgentTask
from app.api.deps import get_current_user
from app.agent.orchestrator import AutonomousStudyAgent
from app.schemas.agent import (
    AgentTaskResponse,
    EvaluateStateRequest,
    ExecuteTaskRequest,
    ExecuteTaskResponse,
    AgentOrchestratorChatRequest,
    AgentOrchestratorChatResponse,
    AdvanceStepRequest,
)

router = APIRouter(prefix="/agent", tags=["Autonomous Study Agent Orchestrator"])


@router.post("/evaluate-state", response_model=AgentTaskResponse)
async def evaluate_state_and_propose_task(
    req: EvaluateStateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates student state across mastery, exam deadlines, and revision urgency,
    proposing the highest-value learning action.
    """
    agent = AutonomousStudyAgent(db_session=db)
    return await agent.evaluate_and_propose_task(
        user_id=current_user.id,
        available_minutes=req.available_minutes,
        days_until_exam=req.days_until_exam or 5,
        subject=req.subject,
    )


@router.post("/execute-task", response_model=ExecuteTaskResponse)
async def execute_task(
    req: ExecuteTaskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes an approved AgentTask by orchestrating existing pedagogical engines
    (Teacher, Practice, Revision, Mastery, Planner).
    """
    agent = AutonomousStudyAgent(db_session=db)
    try:
        return await agent.execute_task(
            user_id=current_user.id,
            task_id=req.task_id,
            auto_apply_planner=req.auto_apply_planner,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/chat", response_model=AgentOrchestratorChatResponse)
async def chat_with_autonomous_agent(
    req: AgentOrchestratorChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Conversational turn with the Autonomous Study Agent.
    Interprets natural student goals (e.g., 'I have 1 hour. Prepare me for tomorrow's exam')
    and synthesizes an orchestrated plan.
    """
    agent = AutonomousStudyAgent(db_session=db)
    return await agent.chat_orchestrator(
        user_id=current_user.id,
        message=req.message,
        available_minutes=req.available_minutes or 60,
    )


@router.get("/tasks", response_model=List[AgentTaskResponse])
async def list_agent_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists recent tasks proposed and executed by the Autonomous Study Agent."""
    res = await db.execute(
        select(AgentTask)
        .where(AgentTask.user_id == current_user.id)
        .order_by(AgentTask.created_at.desc())
        .limit(20)
    )
    tasks = res.scalars().all()
    return [AgentTaskResponse.model_validate(t) for t in tasks]


@router.get("/tasks/{task_id}/explain")
async def explain_task_decision(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Answers 'Why did you choose this?' with transparent pedagogical telemetry."""
    res = await db.execute(
        select(AgentTask).where(AgentTask.id == task_id, AgentTask.user_id == current_user.id)
    )
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    agent = AutonomousStudyAgent(db_session=db)
    explanation = agent.explain_decision(task.explanation_breakdown)
    return {
        "task_id": task.id,
        "goal": task.goal,
        "explanation": explanation,
        "breakdown": task.explanation_breakdown,
    }


@router.get("/active-task", response_model=Optional[AgentTaskResponse])
async def get_active_or_resumable_task(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves ongoing executing or paused task if student reopens app or session restarts."""
    agent = AutonomousStudyAgent(db_session=db)
    return await agent.get_active_task(current_user.id)


@router.post("/tasks/{task_id}/advance", response_model=AgentTaskResponse)
async def advance_task_step(
    task_id: str,
    req: AdvanceStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Records completion of a specific step (e.g. 2 of 3 diagnostic questions) with progress."""
    agent = AutonomousStudyAgent(db_session=db)
    try:
        return await agent.advance_step(
            user_id=current_user.id,
            task_id=task_id,
            step_index=req.step_index,
            step_result=req.step_result,
            mark_task_completed=req.mark_task_completed,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/tasks/{task_id}/pause", response_model=AgentTaskResponse)
async def pause_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pauses task execution state so it survives app closure and device reboots."""
    agent = AutonomousStudyAgent(db_session=db)
    try:
        return await agent.pause_task(user_id=current_user.id, task_id=task_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/tasks/{task_id}/resume")
async def resume_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resumes an interrupted/paused task right where the student left off."""
    agent = AutonomousStudyAgent(db_session=db)
    try:
        return await agent.resume_task(user_id=current_user.id, task_id=task_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/recover", response_model=List[AgentTaskResponse])
async def recover_crashed_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Idempotently recovers any tasks interrupted mid-execution (e.g. app killed / phone reboot)."""
    agent = AutonomousStudyAgent(db_session=db)
    return await agent.recover_interrupted_tasks(user_id=current_user.id)
