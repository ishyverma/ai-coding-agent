from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import EvalResultResponse


router = APIRouter(
    prefix="/evals",
    tags=["evals"],
)


@router.get(
    "",
    response_model=list[EvalResultResponse],
)
def list_eval_results(
    db: Session = Depends(get_db),
) -> list[EvalResultResponse]:
    """List all eval results, newest first."""

    results = crud.list_eval_results(db)

    return [EvalResultResponse.model_validate(result) for result in results]


@router.post(
    "/run",
    status_code=202,
)
def trigger_eval_run(
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Trigger the eval suite to run.

    Returns immediately. Results are saved to the database
    when the run completes.
    """

    background_tasks.add_task(_run_evals_in_background)

    return {
        "message": (
            "Eval run started. Results will appear in " "GET /evals when complete."
        )
    }


def _run_evals_in_background() -> None:
    """Run the full eval suite in the background."""

    from app.database import SessionLocal
    from app.eval.runner import EvalRunner
    from app.eval.scorer import compute_score

    db = SessionLocal()

    try:
        results = EvalRunner().run()
        score = compute_score(results)

        crud.create_eval_result(
            db,
            eval_name="standard",
            total=score.total,
            passed=score.passed,
            failed=score.failed,
            pass_rate=score.pass_rate,
            avg_attempts=score.avg_attempts,
            avg_tokens=score.avg_tokens,
            avg_duration_s=score.avg_duration_s,
        )
        db.commit()
    except Exception as exc:
        print(f"Eval run failed: {exc}")
    finally:
        db.close()
