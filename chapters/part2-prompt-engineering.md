# Part 2: 프롬프트 엔지니어링 (Prompt Engineering)

> 효과적인 AI 활용을 위한 프롬프트 설계 기술

**학습 기간:** 2주
**난이도:** 초급 ~ 중급
**사전 요구사항:** Part 1 완료

---

## 들어가며

"AI에게 어떻게 물어보느냐에 따라 답이 완전히 달라집니다."

이 말이 프롬프트 엔지니어링의 핵심입니다. 같은 AI 모델이라도 질문하는 방법에 따라 평범한 답변을 받을 수도 있고, 전문가 수준의 통찰을 얻을 수도 있습니다.

이 장에서는 AI의 잠재력을 최대한 끌어내는 프롬프트 기법들을 배워봅니다. 템플릿 활용부터 구조화된 출력, 고급 추론 기법까지 - 여러분의 AI 애플리케이션을 한 단계 업그레이드할 준비를 해봅시다!

![Prompt Engineering Patterns](../images/prompt-engineering-patterns.png)

---

## Module 2.1: 프롬프트 템플릿과 변수

### 2.1.1 PromptTemplate 개요

#### 왜 템플릿이 필요할까?

프롬프트를 문자열로 직접 작성하면 이런 문제가 생깁니다:

```kotlin
// ❌ 안 좋은 예: 하드코딩된 프롬프트
fun translate(text: String, language: String): String {
    val prompt = "Translate '$text' to $language"  // SQL Injection과 비슷한 위험!
    return chatClient.prompt().user(prompt).call().content()
}
```

**문제점:**
- 유지보수가 어렵습니다
- 프롬프트 버전 관리가 불가능합니다
- 다국어 지원이 복잡해집니다
- 보안 위험 (프롬프트 인젝션)

**PromptTemplate의 해결책:**

```kotlin
// ✅ 좋은 예: 템플릿 사용
val template = PromptTemplate("""
    You are a professional translator.
    Translate the following text to {language}:

    Text: {text}

    Translation:
""".trimIndent())

val prompt = template.create(mapOf(
    "language" to "Korean",
    "text" to "Hello, World!"
))
```

### 2.1.2 기본 변수 바인딩

#### Map 기반 바인딩

가장 기본적인 방법입니다:

```kotlin
import org.springframework.ai.chat.prompt.PromptTemplate

@Service
class TranslatorService(chatClientBuilder: ChatClient.Builder) {

    private val chatClient = chatClientBuilder.build()

    fun translate(text: String, targetLanguage: String): String {
        // 템플릿 정의
        val template = PromptTemplate("""
            You are an expert translator specializing in natural, fluent translations.

            Translate the following text to {targetLanguage}.
            Maintain the original tone, style, and meaning.

            Original text:
            {text}

            Translation:
        """.trimIndent())

        // 변수 바인딩
        val variables = mapOf(
            "targetLanguage" to targetLanguage,
            "text" to text
        )

        // 프롬프트 생성 및 호출
        val prompt = template.create(variables)
        return chatClient.prompt(prompt).call().content()
    }
}
```

#### 복잡한 데이터 바인딩

리스트나 복잡한 객체도 바인딩할 수 있습니다:

```kotlin
data class ProductInfo(
    val name: String,
    val features: List<String>,
    val targetAudience: String,
    val maxWords: Int
)

@Service
class ProductDescriptionService(chatClientBuilder: ChatClient.Builder) {

    private val chatClient = chatClientBuilder.build()

    fun generateDescription(product: ProductInfo): String {
        val template = PromptTemplate("""
            Write a compelling product description for {name}.

            Key Features:
            {features}

            Target Audience: {targetAudience}
            Maximum Length: {maxWords} words

            The description should be engaging, highlight benefits,
            and speak directly to the target audience.
        """.trimIndent())

        val variables = mapOf(
            "name" to product.name,
            "features" to product.features.joinToString("\n") { "- $it" },
            "targetAudience" to product.targetAudience,
            "maxWords" to product.maxWords.toString()
        )

        return chatClient.prompt(template.create(variables))
            .call()
            .content()
    }
}

// 사용 예
val product = ProductInfo(
    name = "Galaxy S24 Ultra",
    features = listOf(
        "AI 기반 사진 편집",
        "S펜 내장",
        "티타늄 프레임"
    ),
    targetAudience = "기술을 사랑하는 프로페셔널",
    maxWords = 150
)

val description = service.generateDescription(product)
```

### 2.1.3 외부 파일 기반 템플릿

프롬프트가 길어지면 코드에서 분리하는 것이 좋습니다.

#### 프로젝트 구조

```
src/main/resources/
└── prompts/
    ├── system/
    │   ├── translator.st
    │   ├── summarizer.st
    │   └── analyzer.st
    └── user/
        ├── translate-request.st
        └── analyze-request.st
```

#### StringTemplate 파일 작성

```
// prompts/system/translator.st
You are a professional translator specializing in {domain} content.

Your expertise includes:
- {sourceLanguage} to {targetLanguage} translation
- Maintaining technical accuracy
- Preserving cultural nuances

Guidelines:
1. Translate naturally, not word-by-word
2. Keep technical terms when appropriate
3. Maintain the original formatting
4. If unsure about a term, provide alternatives in [brackets]
```

#### 리소스 파일 로딩

```kotlin
import org.springframework.beans.factory.annotation.Value
import org.springframework.core.io.Resource

@Service
class AdvancedTranslatorService(
    chatClientBuilder: ChatClient.Builder,
    @Value("classpath:/prompts/system/translator.st")
    private val translatorPromptResource: Resource
) {
    private val chatClient = chatClientBuilder.build()

    fun translate(
        text: String,
        domain: String = "general",
        sourceLanguage: String = "English",
        targetLanguage: String = "Korean"
    ): String {
        // 리소스에서 템플릿 로드
        val template = PromptTemplate(translatorPromptResource)

        val systemPrompt = template.create(mapOf(
            "domain" to domain,
            "sourceLanguage" to sourceLanguage,
            "targetLanguage" to targetLanguage
        ))

        return chatClient.prompt()
            .system(systemPrompt.contents)
            .user("Translate this: $text")
            .call()
            .content()
    }
}
```

### 2.1.4 프롬프트 라이브러리 패턴

실제 프로젝트에서는 다양한 프롬프트를 체계적으로 관리해야 합니다:

```kotlin
@Component
class PromptLibrary {

    private val templates = mutableMapOf<String, PromptTemplate>()

    @PostConstruct
    fun initialize() {
        // 번역기
        templates["translator"] = PromptTemplate("""
            You are a {domain} translator.
            Translate from {sourceLanguage} to {targetLanguage}.

            Text: {text}

            Translation:
        """.trimIndent())

        // 요약기
        templates["summarizer"] = PromptTemplate("""
            Summarize the following text in {style} style.
            Maximum {maxSentences} sentences.

            Text: {text}

            Summary:
        """.trimIndent())

        // 감정 분석기
        templates["sentiment_analyzer"] = PromptTemplate("""
            Analyze the sentiment of the following text.

            Text: {text}

            Provide:
            1. Overall sentiment (positive/negative/neutral)
            2. Confidence score (0-100)
            3. Key emotional indicators
        """.trimIndent())

        // 코드 리뷰어
        templates["code_reviewer"] = PromptTemplate("""
            Review the following {language} code.

            Focus on:
            - Code quality and best practices
            - Potential bugs or issues
            - Performance considerations
            - Security vulnerabilities

            Code:
            ```{language}
            {code}
            ```

            Provide specific, actionable feedback.
        """.trimIndent())
    }

    fun getPrompt(templateName: String, variables: Map<String, Any>): Prompt {
        val template = templates[templateName]
            ?: throw IllegalArgumentException("Unknown template: $templateName")

        // Any 타입을 String으로 변환
        val stringVariables = variables.mapValues { it.value.toString() }
        return template.create(stringVariables)
    }

    // 템플릿 목록 조회
    fun listTemplates(): Set<String> = templates.keys
}

// 사용 예
@Service
class MultiPurposeAiService(
    chatClientBuilder: ChatClient.Builder,
    private val promptLibrary: PromptLibrary
) {
    private val chatClient = chatClientBuilder.build()

    fun summarize(text: String, style: String = "concise", maxSentences: Int = 3): String {
        val prompt = promptLibrary.getPrompt("summarizer", mapOf(
            "text" to text,
            "style" to style,
            "maxSentences" to maxSentences
        ))
        return chatClient.prompt(prompt).call().content()
    }

    fun reviewCode(code: String, language: String = "kotlin"): String {
        val prompt = promptLibrary.getPrompt("code_reviewer", mapOf(
            "code" to code,
            "language" to language
        ))
        return chatClient.prompt(prompt).call().content()
    }
}
```

---

## Module 2.2: Structured Output (구조화된 출력)

### 2.2.1 왜 구조화된 출력이 필요한가?

AI의 자유로운 텍스트 응답은 사람에게는 좋지만, 프로그램에서 처리하기는 어렵습니다.

```kotlin
// ❌ 비구조화된 응답의 문제
val response = chatClient.prompt()
    .user("'이 제품 정말 좋아요!' 문장의 감정을 분석해주세요")
    .call()
    .content()

// 응답: "이 문장은 긍정적인 감정을 표현하고 있습니다.
//        사용자가 제품에 만족하고 있음을 알 수 있으며,
//        '정말'이라는 강조어를 통해 강한 긍정을 나타내고 있습니다..."

// 이 텍스트에서 "긍정"이라는 정보를 추출하려면? 복잡한 파싱 필요!
```

```kotlin
// ✅ 구조화된 응답의 장점
data class SentimentAnalysis(
    val sentiment: String,      // "positive", "negative", "neutral"
    val confidence: Double,     // 0.0 ~ 1.0
    val keywords: List<String>
)

val result: SentimentAnalysis = chatClient.prompt()
    .user("'이 제품 정말 좋아요!' 문장의 감정을 분석해주세요")
    .call()
    .entity<SentimentAnalysis>()

// 바로 사용 가능!
println("감정: ${result.sentiment}")     // "positive"
println("신뢰도: ${result.confidence}")  // 0.95
```

### 2.2.2 entity() 메서드 활용

Spring AI의 `entity()` 메서드는 AI 응답을 자동으로 객체로 변환합니다.

#### 기본 사용법

```kotlin
import org.springframework.ai.chat.client.entity

// 응답 형식 정의
data class MovieReview(
    val title: String,
    val rating: Int,           // 1-5
    val summary: String,
    val pros: List<String>,
    val cons: List<String>,
    val recommended: Boolean
)

@Service
class MovieReviewService(chatClientBuilder: ChatClient.Builder) {

    private val chatClient = chatClientBuilder.build()

    fun analyzeReview(reviewText: String): MovieReview {
        return chatClient.prompt()
            .user("""
                Analyze this movie review and extract structured information:

                Review: "$reviewText"

                Extract: title, rating (1-5), summary, pros, cons, and recommendation.
            """.trimIndent())
            .call()
            .entity<MovieReview>()  // Kotlin의 reified type 활용
    }
}

// 사용 예
val review = service.analyzeReview("""
    인셉션은 정말 대작입니다! 시각 효과가 압도적이고,
    스토리가 복잡하지만 보람 있습니다. 다만 처음 볼 때는
    좀 혼란스러울 수 있어요. 10점 만점에 9점!
""".trimIndent())

println(review.title)        // "인셉션"
println(review.rating)       // 5 (또는 4-5 사이)
println(review.pros)         // ["압도적인 시각 효과", "보람 있는 스토리"]
println(review.cons)         // ["처음 볼 때 혼란스러움"]
println(review.recommended)  // true
```

#### 리스트 응답 처리

```kotlin
import org.springframework.core.ParameterizedTypeReference

data class Task(
    val title: String,
    val priority: String,  // HIGH, MEDIUM, LOW
    val deadline: String?
)

@Service
class TaskExtractorService(chatClientBuilder: ChatClient.Builder) {

    private val chatClient = chatClientBuilder.build()

    fun extractTasks(emailContent: String): List<Task> {
        return chatClient.prompt()
            .user("""
                Extract all tasks mentioned in this email:

                $emailContent

                For each task, identify the title, priority level, and deadline if mentioned.
            """.trimIndent())
            .call()
            .entity(object : ParameterizedTypeReference<List<Task>>() {})
    }
}
```

### 2.2.3 스키마 어노테이션으로 정확도 높이기

`@JsonPropertyDescription`을 사용하면 AI가 각 필드의 의미를 더 잘 이해합니다:

```kotlin
import com.fasterxml.jackson.annotation.JsonProperty
import com.fasterxml.jackson.annotation.JsonPropertyDescription

data class ProductAnalysis(
    @JsonPropertyDescription("Product name extracted from the review")
    val productName: String,

    @JsonPropertyDescription("Overall rating from 1 to 5 stars")
    @JsonProperty(required = true)
    val rating: Int,

    @JsonPropertyDescription("List of positive aspects mentioned by the reviewer")
    val positives: List<String>,

    @JsonPropertyDescription("List of negative aspects or complaints")
    val negatives: List<String>,

    @JsonPropertyDescription("Whether the reviewer recommends this product to others")
    val recommended: Boolean,

    @JsonPropertyDescription("Key phrases that indicate the reviewer's sentiment")
    val sentimentIndicators: List<String>
)
```

#### Enum 활용으로 값 제한

```kotlin
enum class Priority {
    LOW,
    MEDIUM,
    HIGH,
    URGENT
}

enum class IssueCategory {
    BUG,
    FEATURE_REQUEST,
    IMPROVEMENT,
    QUESTION,
    DOCUMENTATION
}

data class IssueClassification(
    @JsonPropertyDescription("The type of issue being reported")
    val category: IssueCategory,

    @JsonPropertyDescription("How urgent this issue is")
    val priority: Priority,

    @JsonPropertyDescription("Brief one-line summary of the issue")
    val summary: String,

    @JsonPropertyDescription("Suggested tags for this issue")
    val tags: List<String>,

    @JsonPropertyDescription("Estimated effort: SMALL (< 1 day), MEDIUM (1-3 days), LARGE (> 3 days)")
    val estimatedEffort: String
)

// AI는 자동으로 enum 값 중에서 선택합니다
val classification = chatClient.prompt()
    .user("""
        Classify this GitHub issue:

        Title: App crashes when clicking submit button
        Description: When I click the submit button on the registration form,
        the app crashes with a NullPointerException. This started after the
        latest update. Very frustrating as I can't complete registration!
    """.trimIndent())
    .call()
    .entity<IssueClassification>()

// classification.category == IssueCategory.BUG
// classification.priority == Priority.HIGH
```

### 2.2.4 복잡한 중첩 구조

실제 비즈니스에서는 복잡한 데이터 구조가 필요합니다:

```kotlin
// 중첩된 데이터 클래스 정의
data class Author(
    val name: String,
    val email: String?,
    val affiliation: String?
)

data class Chapter(
    val number: Int,
    val title: String,
    val pageCount: Int,
    val topics: List<String>
)

data class BookAnalysis(
    val title: String,
    val authors: List<Author>,
    val chapters: List<Chapter>,
    val genre: String,
    val publicationYear: Int?,
    val targetAudience: String,
    val summary: String,
    val keyTakeaways: List<String>
)

@Service
class BookAnalyzerService(chatClientBuilder: ChatClient.Builder) {

    private val chatClient = chatClientBuilder.build()

    fun analyzeBook(bookDescription: String): BookAnalysis {
        return chatClient.prompt()
            .system("""
                You are a professional book analyst.
                Extract detailed structured information from book descriptions.
                Be thorough but accurate - only include information that is clearly stated or can be reasonably inferred.
            """.trimIndent())
            .user("Analyze this book: $bookDescription")
            .call()
            .entity<BookAnalysis>()
    }
}
```

### 2.2.5 유효성 검증

AI 응답도 검증이 필요합니다:

```kotlin
import jakarta.validation.constraints.*
import jakarta.validation.Validator

data class RegistrationForm(
    @field:NotBlank(message = "이름은 필수입니다")
    @field:Size(min = 2, max = 50, message = "이름은 2-50자여야 합니다")
    val name: String,

    @field:Email(message = "유효한 이메일 형식이 아닙니다")
    val email: String,

    @field:Min(value = 18, message = "18세 이상이어야 합니다")
    @field:Max(value = 120, message = "유효한 나이를 입력해주세요")
    val age: Int,

    @field:Pattern(
        regexp = "^010-\\d{4}-\\d{4}$",
        message = "전화번호 형식: 010-XXXX-XXXX"
    )
    val phone: String?
)

@Service
class FormExtractionService(
    chatClientBuilder: ChatClient.Builder,
    private val validator: Validator
) {
    private val chatClient = chatClientBuilder.build()

    fun extractForm(naturalLanguageInput: String): RegistrationForm {
        // 1. AI로 정보 추출
        val form = chatClient.prompt()
            .user("""
                Extract registration information from this text:
                "$naturalLanguageInput"

                If phone number is mentioned, format it as 010-XXXX-XXXX.
                If age is not explicitly mentioned, make a reasonable inference if possible.
            """.trimIndent())
            .call()
            .entity<RegistrationForm>()

        // 2. 유효성 검증
        val violations = validator.validate(form)
        if (violations.isNotEmpty()) {
            val errors = violations.joinToString(", ") { it.message }
            throw ValidationException("Form validation failed: $errors")
        }

        return form
    }
}

// 사용 예
val form = service.extractForm("""
    안녕하세요, 저는 김철수입니다.
    이메일은 chulsoo@gmail.com이고,
    올해 25살이에요.
    연락처는 010-1234-5678입니다.
""".trimIndent())
```

### 2.2.6 실습: 이력서 파서

실제 업무에서 유용한 이력서 분석 서비스를 만들어봅시다:

```kotlin
// 데이터 모델 정의
data class PersonalInfo(
    val name: String,
    val email: String?,
    val phone: String?,
    val location: String?,
    val linkedIn: String?,
    val github: String?
)

data class Education(
    val institution: String,
    val degree: String,
    val field: String,
    val graduationYear: String?,
    val gpa: String?
)

data class Experience(
    val company: String,
    val position: String,
    val startDate: String,
    val endDate: String?,  // null이면 현재 재직 중
    val responsibilities: List<String>,
    val achievements: List<String>
)

data class Resume(
    val personal: PersonalInfo,
    val summary: String?,
    val education: List<Education>,
    val experience: List<Experience>,
    val skills: List<String>,
    val certifications: List<String>,
    val languages: List<String>
)

@Service
class ResumeParserService(chatClientBuilder: ChatClient.Builder) {

    private val chatClient = chatClientBuilder
        .defaultSystem("""
            You are an expert resume parser with extensive experience in HR and recruiting.

            Your task is to extract structured information from resumes.

            Guidelines:
            - Extract all available information accurately
            - Use null for fields that are not mentioned
            - Parse dates in YYYY-MM format when possible
            - List skills as individual items, not grouped
            - Separate achievements from responsibilities in work experience
            - Be thorough but don't make up information
        """.trimIndent())
        .build()

    fun parseResume(resumeText: String): Resume {
        return chatClient.prompt()
            .user("""
                Parse this resume and extract all information:

                ---
                $resumeText
                ---

                Extract: personal info, professional summary, education history,
                work experience (with responsibilities and achievements separated),
                skills, certifications, and language proficiencies.
            """.trimIndent())
            .call()
            .entity<Resume>()
    }

    // 특정 정보만 추출
    fun extractSkills(resumeText: String): List<String> {
        data class SkillsOnly(val skills: List<String>)

        return chatClient.prompt()
            .user("Extract all technical and soft skills from this resume: $resumeText")
            .call()
            .entity<SkillsOnly>()
            .skills
    }

    // 경력 요약
    fun summarizeExperience(resumeText: String): String {
        return chatClient.prompt()
            .user("""
                Based on this resume, write a brief (2-3 sentences)
                professional summary highlighting key qualifications:

                $resumeText
            """.trimIndent())
            .call()
            .content()
    }
}
```

---

## Module 2.3: 고급 프롬프트 기법

### 2.3.1 Zero-shot vs Few-shot

#### Zero-shot: 예시 없이 바로 질문

```kotlin
// Zero-shot - 예시 없이 직접 요청
val response = chatClient.prompt()
    .user("""
        Classify the following text into one of these categories:
        [Technology, Sports, Politics, Entertainment, Science]

        Text: "Apple announced the new iPhone 16 with AI features at their annual event."

        Category:
    """.trimIndent())
    .call()
    .content()

// 결과: "Technology"
```

**장점:** 빠르고 간단
**단점:** 복잡한 작업에서는 정확도가 낮을 수 있음

#### Few-shot: 예시로 패턴 학습

```kotlin
// Few-shot - 예시를 통해 패턴 학습
val response = chatClient.prompt()
    .user("""
        Classify texts into categories.

        Examples:
        ---
        Text: "The Lakers dominated the championship game with a 30-point lead."
        Category: Sports

        Text: "The new tax bill passed in Congress with bipartisan support."
        Category: Politics

        Text: "Marvel's latest movie broke all box office records this weekend."
        Category: Entertainment

        Text: "Scientists discovered a new species of deep-sea fish near the Mariana Trench."
        Category: Science
        ---

        Now classify:
        Text: "Apple announced the new iPhone 16 with AI features at their annual event."
        Category:
    """.trimIndent())
    .call()
    .content()
```

**Few-shot이 효과적인 경우:**
- 특정 형식의 출력이 필요할 때
- 도메인 특화 분류가 필요할 때
- AI가 새로운 개념을 이해해야 할 때

### 2.3.2 Chain-of-Thought (CoT) 추론

복잡한 문제는 단계별로 생각하게 하면 정확도가 높아집니다.

#### 기본 CoT

```kotlin
// 단순 질문 - 오답 가능성 높음
val simpleAnswer = chatClient.prompt()
    .user("""
        상점에 사과가 45개 있습니다.
        오전에 12개를 팔고, 30개를 추가로 받았습니다.
        오후에 18개를 더 팔았습니다.
        남은 사과는 몇 개인가요?
    """.trimIndent())
    .call()
    .content()

// CoT 적용 - 단계별 추론으로 정확도 향상
val cotAnswer = chatClient.prompt()
    .user("""
        상점에 사과가 45개 있습니다.
        오전에 12개를 팔고, 30개를 추가로 받았습니다.
        오후에 18개를 더 팔았습니다.
        남은 사과는 몇 개인가요?

        단계별로 생각해봅시다:
    """.trimIndent())
    .call()
    .content()

// AI 응답:
// 단계별로 생각해봅시다:
// 1. 초기 사과 수: 45개
// 2. 오전에 12개 판매: 45 - 12 = 33개
// 3. 30개 추가 입고: 33 + 30 = 63개
// 4. 오후에 18개 판매: 63 - 18 = 45개
// 따라서 남은 사과는 45개입니다.
```

#### Zero-shot CoT

간단히 "단계별로 생각해봅시다"만 추가해도 효과가 있습니다:

```kotlin
fun solveWithReasoning(problem: String): String {
    return chatClient.prompt()
        .user("""
            $problem

            Let's think step by step.
        """.trimIndent())
        .call()
        .content()
}
```

#### 구조화된 CoT

추론 과정을 객체로 받아 검증할 수 있습니다:

```kotlin
data class ReasoningStep(
    val stepNumber: Int,
    val description: String,
    val calculation: String?,
    val result: String
)

data class ReasoningResult(
    val steps: List<ReasoningStep>,
    val finalAnswer: String,
    val confidence: Double
)

@Service
class ReasoningService(chatClientBuilder: ChatClient.Builder) {

    private val chatClient = chatClientBuilder
        .defaultSystem("""
            You are a logical reasoning assistant.
            Always break down problems into clear, numbered steps.
            Show your work and explain each step.
            Provide a confidence score (0-1) for your final answer.
        """.trimIndent())
        .build()

    fun solveWithStructuredReasoning(problem: String): ReasoningResult {
        return chatClient.prompt()
            .user("""
                Solve this problem with detailed step-by-step reasoning:

                $problem

                Provide each step with:
                - Step number
                - Description of what you're doing
                - Calculation (if applicable)
                - Intermediate result

                Then provide the final answer and your confidence level.
            """.trimIndent())
            .call()
            .entity<ReasoningResult>()
    }
}
```

### 2.3.3 Self-Consistency (자기 일관성)

동일한 질문을 여러 번 하고, 가장 많이 나온 답을 선택하는 기법입니다:

```kotlin
import org.springframework.ai.openai.OpenAiChatOptions

@Service
class SelfConsistencyService(chatClientBuilder: ChatClient.Builder) {

    private val chatClient = chatClientBuilder.build()

    fun solveWithConsistency(problem: String, samples: Int = 5): ConsistencyResult {
        val answers = mutableMapOf<String, Int>()
        val allResponses = mutableListOf<String>()

        repeat(samples) {
            val response = chatClient.prompt()
                .user("""
                    $problem

                    Think step by step, then provide your final answer on the last line
                    starting with "ANSWER: "
                """.trimIndent())
                .options(OpenAiChatOptions.builder()
                    .temperature(0.7)  // 다양한 추론 경로를 위해 약간의 랜덤성
                    .build())
                .call()
                .content()

            allResponses.add(response)

            // 최종 답변 추출
            val answer = extractFinalAnswer(response)
            answers[answer] = answers.getOrDefault(answer, 0) + 1
        }

        // 가장 많이 나온 답변 선택
        val bestAnswer = answers.maxByOrNull { it.value }!!
        val confidence = bestAnswer.value.toDouble() / samples

        return ConsistencyResult(
            answer = bestAnswer.key,
            confidence = confidence,
            voteDistribution = answers,
            allResponses = allResponses
        )
    }

    private fun extractFinalAnswer(response: String): String {
        val answerLine = response.lines()
            .lastOrNull { it.startsWith("ANSWER:") }
        return answerLine?.substringAfter("ANSWER:")?.trim() ?: "Unknown"
    }
}

data class ConsistencyResult(
    val answer: String,
    val confidence: Double,
    val voteDistribution: Map<String, Int>,
    val allResponses: List<String>
)
```

### 2.3.4 역할 기반 프롬프팅 (Role-Playing)

AI에게 전문가 역할을 부여하면 더 전문적인 답변을 얻을 수 있습니다:

```kotlin
@Service
class ExpertPanelService(chatClientBuilder: ChatClient.Builder) {

    private val chatClient = chatClientBuilder.build()

    // 단일 전문가 페르소나
    fun getSecurityReview(code: String): String {
        return chatClient.prompt()
            .system("""
                You are a senior security engineer with 15 years of experience
                in application security. You have:

                - CISSP, CEH, and OSCP certifications
                - Extensive experience with OWASP Top 10 vulnerabilities
                - Background in penetration testing and secure code review
                - Worked at major tech companies on security-critical systems

                Your review style is:
                - Thorough and systematic
                - Practical, focusing on real-world exploitability
                - Educational, explaining why issues are problematic
                - Prioritized by severity
            """.trimIndent())
            .user("Review this code for security vulnerabilities:\n$code")
            .call()
            .content()
    }

    // 다중 전문가 협업 (Multi-Expert Panel)
    fun getComprehensiveReview(proposal: String): ComprehensiveReview {
        // 기술 전문가 관점
        val technicalView = chatClient.prompt()
            .system("You are a senior software architect focusing on technical feasibility, scalability, and implementation complexity.")
            .user("Evaluate this proposal from a technical perspective:\n$proposal")
            .call()
            .content()

        // 비즈니스 전문가 관점
        val businessView = chatClient.prompt()
            .system("You are a business analyst focusing on ROI, market fit, competitive advantage, and revenue potential.")
            .user("Evaluate this proposal from a business perspective:\n$proposal")
            .call()
            .content()

        // 보안 전문가 관점
        val securityView = chatClient.prompt()
            .system("You are a security expert focusing on data privacy, compliance requirements, and potential vulnerabilities.")
            .user("Evaluate this proposal from a security perspective:\n$proposal")
            .call()
            .content()

        // 종합 (프로젝트 매니저 역할)
        val synthesis = chatClient.prompt()
            .system("""
                You are an experienced project manager who synthesizes expert opinions.
                Your role is to:
                - Identify areas of agreement and disagreement
                - Balance technical, business, and security concerns
                - Provide actionable recommendations
                - Highlight key risks and opportunities
            """.trimIndent())
            .user("""
                Based on these expert analyses, provide a balanced recommendation:

                ## Technical Analysis
                $technicalView

                ## Business Analysis
                $businessView

                ## Security Analysis
                $securityView

                Synthesize these perspectives into a final recommendation.
            """.trimIndent())
            .call()
            .content()

        return ComprehensiveReview(
            technical = technicalView,
            business = businessView,
            security = securityView,
            synthesis = synthesis
        )
    }
}

data class ComprehensiveReview(
    val technical: String,
    val business: String,
    val security: String,
    val synthesis: String
)
```

### 2.3.5 실습: 복잡한 추론 문제 해결 봇

모든 기법을 종합한 고급 추론 봇을 만들어봅시다:

```kotlin
@Service
class AdvancedReasoningBot(chatClientBuilder: ChatClient.Builder) {

    private val chatClient = chatClientBuilder.build()

    fun solve(problem: String): ReasoningResponse {
        // 1단계: 문제 분석
        val analysis = analyzeProblem(problem)
        println("📋 문제 분석 완료: ${analysis.problemType}")

        // 2단계: 단계별 해결 (Chain-of-Thought)
        val steps = solveStepByStep(problem, analysis)
        println("🔢 ${steps.size}개 단계로 해결 시도")

        // 3단계: 자기 검증 (Self-Verification)
        val verification = verifySolution(problem, steps)
        println("✅ 검증 결과: ${if (verification.isCorrect) "정확" else "재검토 필요"}")

        // 4단계: 필요시 재시도
        val finalSteps = if (!verification.isCorrect && verification.confidence < 0.7) {
            println("🔄 신뢰도 낮음, 다른 접근법으로 재시도...")
            solveStepByStep(problem, analysis, alternativeApproach = true)
        } else {
            steps
        }

        val finalVerification = verifySolution(problem, finalSteps)

        return ReasoningResponse(
            problemAnalysis = analysis,
            solutionSteps = finalSteps,
            finalAnswer = finalSteps.lastOrNull()?.result ?: "해결 실패",
            verification = finalVerification
        )
    }

    private fun analyzeProblem(problem: String): ProblemAnalysis {
        return chatClient.prompt()
            .system("""
                You are a problem analysis expert.
                Analyze the given problem and identify:
                - Problem type (math, logic, word problem, etc.)
                - Key information provided
                - What is being asked
                - Potential approaches to solve it
            """.trimIndent())
            .user(problem)
            .call()
            .entity<ProblemAnalysis>()
    }

    private fun solveStepByStep(
        problem: String,
        analysis: ProblemAnalysis,
        alternativeApproach: Boolean = false
    ): List<SolutionStep> {
        val approachHint = if (alternativeApproach) {
            "Try a different approach than the obvious one. Consider working backwards or using a different method."
        } else {
            "Use the most straightforward approach."
        }

        return chatClient.prompt()
            .system("""
                You are a methodical problem solver.
                Solve problems step by step, showing all work.

                For each step:
                1. State what you're doing
                2. Show the calculation or reasoning
                3. State the intermediate result

                $approachHint
            """.trimIndent())
            .user("""
                Problem: $problem

                Analysis: ${analysis.problemType} - ${analysis.goal}
                Key info: ${analysis.givenInfo.joinToString(", ")}

                Solve step by step:
            """.trimIndent())
            .call()
            .entity<SolutionSteps>()
            .steps
    }

    private fun verifySolution(problem: String, steps: List<SolutionStep>): Verification {
        return chatClient.prompt()
            .system("""
                You are a verification expert.
                Check if the solution is correct by:
                1. Reviewing each step's logic
                2. Checking calculations
                3. Verifying the answer makes sense
                4. Testing with the original problem constraints
            """.trimIndent())
            .user("""
                Original problem: $problem

                Solution steps:
                ${steps.mapIndexed { i, s -> "${i+1}. ${s.description}: ${s.result}" }.joinToString("\n")}

                Verify this solution:
            """.trimIndent())
            .call()
            .entity<Verification>()
    }
}

// 데이터 클래스들
data class ProblemAnalysis(
    val problemType: String,
    val givenInfo: List<String>,
    val goal: String,
    val suggestedApproaches: List<String>
)

data class SolutionStep(
    val stepNumber: Int,
    val description: String,
    val calculation: String?,
    val result: String
)

data class SolutionSteps(val steps: List<SolutionStep>)

data class Verification(
    val isCorrect: Boolean,
    val confidence: Double,
    val explanation: String,
    val issues: List<String>
)

data class ReasoningResponse(
    val problemAnalysis: ProblemAnalysis,
    val solutionSteps: List<SolutionStep>,
    val finalAnswer: String,
    val verification: Verification
)
```

---

## Part 2 요약

### 이 파트에서 배운 것

#### 프롬프트는 AI 애플리케이션의 핵심 인터페이스

프롬프트 엔지니어링은 단순한 문자열 조합이 아니라 **AI와의 계약(Contract)**을 설계하는 작업입니다. PromptTemplate을 통해 재사용 가능한 프롬프트를 정의하고, 변수 바인딩으로 동적 컨텍스트를 주입하는 패턴은 유지보수성과 테스트 용이성을 크게 향상시킵니다. 프롬프트를 외부 리소스로 분리하면 코드 변경 없이 AI 동작을 조정할 수 있어 운영 유연성이 확보됩니다.

#### Structured Output: 비정형에서 정형으로

AI의 자연어 응답을 프로그래밍 가능한 데이터로 변환하는 것은 실용적인 AI 애플리케이션의 필수 요소입니다. Spring AI의 `entity()` 메서드와 Kotlin data class를 결합하면 **타입 안전성**을 유지하면서 AI 응답을 도메인 객체로 직접 매핑할 수 있습니다. 이는 JSON 파싱의 복잡성을 추상화하고, 컴파일 타임에 응답 구조를 검증할 수 있게 합니다.

#### 고급 프롬프팅 기법의 전략적 활용

Few-shot Learning은 예시를 통해 AI에게 암묵적 규칙을 학습시키는 기법으로, 일관된 출력 형식이 필요한 경우에 효과적입니다. Chain-of-Thought(CoT)는 AI가 중간 추론 과정을 명시하도록 유도하여 복잡한 문제의 정확도를 높입니다. Self-Consistency는 다중 샘플링과 앙상블 투표로 신뢰도를 향상시키며, 비용과 정확도 사이의 트레이드오프를 고려해야 합니다. 이러한 기법들은 상호 배타적이지 않으며, 문제의 특성에 따라 조합하여 사용할 수 있습니다.

### 핵심 개념 정리

| 기법 | 설명 | 사용 시점 |
|------|------|----------|
| **PromptTemplate** | 재사용 가능한 프롬프트 템플릿. 변수 치환과 외부 리소스 로딩 지원 | 동적 프롬프트, 다국어 지원, A/B 테스트 |
| **Structured Output** | AI 응답을 타입 안전한 객체로 변환. JSON Schema 기반 검증 | API 응답, 데이터 파이프라인, 폼 자동 완성 |
| **Few-shot** | 예시 기반 In-context Learning. 패턴 인식을 통한 형식 학습 | 일관된 형식, 도메인 특화 어휘, 스타일 모방 |
| **Chain-of-Thought** | 단계별 추론 유도. "Let's think step by step" 패턴 | 수학/논리 문제, 복잡한 의사결정, 디버깅 |
| **Self-Consistency** | 다중 샘플링 후 다수결 투표. 앙상블 기법의 LLM 적용 | 높은 정확도 필수, 모호한 문제, 검증 필요 시 |
| **Role-Playing** | 전문가 페르소나 부여. 도메인 지식 활성화 | 전문 분야 상담, 시뮬레이션, 교육 콘텐츠 |

### 실전 활용 팁

#### 프롬프트 설계 원칙
- **명확성(Clarity)**: 모호한 표현을 피하고 구체적인 지시를 제공하세요
- **구조화(Structure)**: 복잡한 요구사항은 번호 매기기나 섹션으로 구분하세요
- **제약 조건(Constraints)**: 원하지 않는 동작을 명시적으로 금지하세요

#### Structured Output 사용 시
- **중첩 객체 활용**: 복잡한 응답은 계층적 data class로 모델링하세요
- **Optional 필드**: 선택적 정보는 nullable 타입으로 정의하세요
- **검증 로직 분리**: 비즈니스 검증은 매핑 후 별도 레이어에서 수행하세요

### 자주 하는 실수

| 실수 | 문제점 | 해결 방법 |
|------|--------|----------|
| 프롬프트 하드코딩 | 수정 시 재배포 필요, 버전 관리 어려움 | 외부 리소스 파일로 분리 |
| 과도한 Few-shot 예시 | 토큰 낭비, 컨텍스트 윈도우 초과 | 2-3개의 대표적인 예시만 사용 |
| CoT 남용 | 단순 문제에 불필요한 오버헤드 | 복잡도에 따라 선택적 적용 |
| Structured Output 과신 | AI가 항상 유효한 JSON을 반환한다고 가정 | 파싱 실패 대비 예외 처리 구현 |

### 학습 체크리스트

- [ ] PromptTemplate 생성 및 변수 바인딩
- [ ] 외부 파일 기반 프롬프트 관리
- [ ] entity()를 통한 구조화된 출력
- [ ] data class 기반 응답 모델링
- [ ] Few-shot 프롬프팅 구현
- [ ] Chain-of-Thought 추론
- [ ] 다중 전문가 패널 구현

### 다음 단계

Part 2에서 AI의 응답 품질을 높이는 프롬프트 기법을 익혔다면, 이제 AI에게 **실행 능력**을 부여할 차례입니다.

**Part 3: Function Calling과 도구 통합**에서 배울 내용:

| 주제 | 설명 | 활용 예시 |
|------|------|----------|
| **Function Callback** | AI가 외부 함수를 호출하도록 정의 | 날씨 조회, 환율 계산, DB 검색 |
| **@Description 어노테이션** | 함수 메타데이터를 AI에게 전달 | 파라미터 설명, 사용 조건 명시 |
| **멀티 함수 시나리오** | 여러 도구를 조합한 복잡한 작업 | 예약 시스템, 주문 처리 워크플로우 |
| **Advisors 패턴** | 요청/응답 파이프라인 커스터마이징 | 로깅, 검증, 캐싱, 컨텍스트 주입 |

Function Calling은 AI를 단순한 텍스트 생성기에서 **자율적인 에이전트**로 전환시키는 핵심 기술입니다!

---

## 참고 예제 코드

```
spring-ai-examples/
├── prompt-engineering/prompt-engineering-patterns  → 다양한 프롬프트 기법
├── agentic-patterns/routing-workflow              → Structured Output 활용
└── agentic-patterns/evaluator-optimizer           → 평가 기반 개선 패턴
```
