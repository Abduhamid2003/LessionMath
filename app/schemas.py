from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6)
    full_name: str = ""


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=6)


class PlotRequest(BaseModel):
    expression: str
    x_min: float = -10
    x_max: float = 10
    points: int = Field(default=400, le=2000)


class MultiPlotRequest(BaseModel):
    expressions: list[str] = Field(min_length=1, max_length=5)
    x_min: float = -10
    x_max: float = 10
    points: int = Field(default=400, le=2000)


class LimitRequest(BaseModel):
    expression: str
    point: float = 0
    direction: str = "both"


class TaylorRequest(BaseModel):
    expression: str
    x0: float = 0
    order: int = Field(default=5, ge=1, le=12)


class CheckDerivativeRequest(BaseModel):
    expression: str
    user_answer: str


class DerivativeRequest(BaseModel):
    expression: str
    order: int = 1


class TangentRequest(BaseModel):
    expression: str
    x0: float
    x_range: float = 5


class IntegralRequest(BaseModel):
    expression: str
    a: float
    b: float
    method: str = "symbolic"


class PreferencesUpdate(BaseModel):
    preferred_language: str | None = None
    preferred_theme: str | None = None


class FormulaCreate(BaseModel):
    expression: str
    label: str = ""
    is_favorite: bool = False


class LessonCreate(BaseModel):
    title_ru: str
    title_tg: str = ""
    title_en: str = ""
    content_ru: str
    content_tg: str = ""
    content_en: str = ""
    category: str = "general"
    order_index: int = 0
    image_urls: list[str] = []


class LessonUpdate(BaseModel):
    title_ru: str | None = None
    title_tg: str | None = None
    title_en: str | None = None
    content_ru: str | None = None
    content_tg: str | None = None
    content_en: str | None = None
    category: str | None = None
    order_index: int | None = None
    image_urls: list[str] | None = None
    is_published: bool | None = None


class TestCreate(BaseModel):
    title_ru: str
    title_tg: str = ""
    title_en: str = ""
    description_ru: str = ""
    description_tg: str = ""
    description_en: str = ""
    category: str = "derivatives"
    max_score: int = 100
    class_id: int | None = None


class TestUpdate(BaseModel):
    title_ru: str | None = None
    title_tg: str | None = None
    title_en: str | None = None
    description_ru: str | None = None
    description_tg: str | None = None
    description_en: str | None = None
    category: str | None = None
    max_score: int | None = None
    class_id: int | None = None
    is_published: bool | None = None


class TestQuestionCreate(BaseModel):
    question_ru: str
    question_tg: str = ""
    question_en: str = ""
    options_ru: list[str]
    options_tg: list[str] | None = None
    options_en: list[str] | None = None
    correct_answer: int
    points: int = 10
    hint_ru: str = ""
    hint_tg: str = ""
    hint_en: str = ""


class TestQuestionUpdate(BaseModel):
    question_ru: str | None = None
    question_tg: str | None = None
    question_en: str | None = None
    options_ru: list[str] | None = None
    options_tg: list[str] | None = None
    options_en: list[str] | None = None
    correct_answer: int | None = None
    points: int | None = None
    hint_ru: str | None = None
    hint_tg: str | None = None
    hint_en: str | None = None


class TestImportPayload(BaseModel):
    title_ru: str
    title_tg: str = ""
    title_en: str = ""
    description_ru: str = ""
    category: str = "derivatives"
    class_id: int | None = None
    questions: list[TestQuestionCreate]


class NumericEvalRequest(BaseModel):
    expression: str


class FunctionEvalRequest(BaseModel):
    expression: str
    x: float


class TestSubmit(BaseModel):
    answers: dict[int, int]
