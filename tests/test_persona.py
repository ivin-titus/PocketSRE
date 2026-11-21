from app.persona.presentation import Language, Persona, Presentation, detect_language
from app.shared.contracts import ActionRequest, ActorRole, RunbookAction


def test_detect_language_and_code_mixing_without_paid_speech_provider() -> None:
    assert detect_language("is core api healthy?") is Language.ENGLISH
    assert detect_language("क्या core api ठीक है?") is Language.HINDI
    assert detect_language("core api ശരിയാണോ?") is Language.MALAYALAM
    assert detect_language("core api down hai, check karo") is Language.HINGLISH
    assert detect_language("core api down aayi, onnu nokk") is Language.MANGLISH


def test_personas_change_presentation_not_action_contract() -> None:
    kiwi = Presentation(Persona.KIWI, Language.MANGLISH)
    vikram = Presentation(Persona.VIKRAM, Language.MANGLISH)
    assert kiwi.incident_title("P2", "yuki-core-api") != vikram.incident_title("P2", "yuki-core-api")
    assert "attention" in kiwi.incident_intro("yuki-core-api")
    request = ActionRequest(
        incident_id="00000000-0000-0000-0000-000000000001",
        action=RunbookAction.RESTART_SERVICE,
        service="yuki-core-api",
        actor_id="operator",
        actor_role=ActorRole.LEAD,
        approved=True,
    )
    assert request.action is RunbookAction.RESTART_SERVICE
    assert request.service == "yuki-core-api"
