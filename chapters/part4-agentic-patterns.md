# Part 4: Agentic Patterns (에이전트 패턴)

> 자율적으로 작업을 수행하는 AI 에이전트 구축

**학습 기간:** 3주
**난이도:** 중급 ~ 고급
**사전 요구사항:** Part 1, 2, 3 완료

---

## 들어가며

지금까지 우리는 Spring AI의 기초, 프롬프트 엔지니어링, 그리고 Function Calling을 배웠습니다. 이제 한 단계 더 나아가 **AI 에이전트**의 세계로 들어갑니다.

AI 에이전트란 무엇일까요? 단순히 질문에 답하는 챗봇을 넘어, **스스로 생각하고, 계획하고, 실행하는** AI 시스템입니다. 마치 숙련된 직원처럼 복잡한 작업을 여러 단계로 나누고, 각 단계를 수행하며, 필요하면 다시 계획을 수정하기도 합니다.

![Agentic Patterns](../images/agentic-patterns.png)

이번 파트에서는 6가지 핵심 에이전트 패턴을 배웁니다:

1. **Chain Workflow** - 순차적 작업 처리
2. **Parallelization** - 병렬 작업 처리
3. **Routing** - 조건에 따른 분기 처리
4. **Orchestrator-Workers** - 동적 작업 분배
5. **Evaluator-Optimizer** - 반복적 품질 개선
6. **Reflection** - 자기 반성을 통한 개선

---

## Module 4.1: Chain Workflow (체인 워크플로우)

### 4.1.1 Chain Workflow 개념

**체인 워크플로우**는 가장 직관적인 에이전트 패턴입니다. 복잡한 작업을 여러 단계로 나누고, 각 단계를 **순차적으로** 실행합니다. 앞 단계의 출력이 다음 단계의 입력이 됩니다.

```
Input → [Step 1] → [Step 2] → [Step 3] → Output
           ↓          ↓          ↓
        Output 1   Output 2   Output 3
        (Input 2)  (Input 3)  (Final)
```

#### 왜 체인이 필요할까요?

하나의 복잡한 프롬프트로 모든 것을 처리하려 하면 AI가 혼란스러워할 수 있습니다. 대신 작업을 단순한 단계로 나누면:

- **정확도 향상**: 각 단계에서 하나의 명확한 목표만 수행
- **디버깅 용이**: 어떤 단계에서 문제가 생겼는지 쉽게 파악
- **유연성**: 필요에 따라 단계를 추가하거나 제거 가능

#### 실제 사용 사례

- **문서 생성**: 주제 분석 → 개요 작성 → 본문 작성 → 편집
- **코드 리뷰**: 코드 분석 → 문제점 식별 → 개선안 제시
- **번역**: 원문 분석 → 초벌 번역 → 문맥 다듬기 → 최종 검수

### 4.1.2 기본 구현

가장 간단한 형태의 체인 워크플로우를 Kotlin으로 구현해 봅시다.

```kotlin
@Service
class SimpleChainWorkflow(
    private val chatClient: ChatClient
) {

    fun process(input: String): String {
        // Step 1: 텍스트 분석
        val analysis = chatClient.prompt()
            .system("주어진 텍스트를 분석하고 핵심 주제를 파악하세요.")
            .user(input)
            .call()
            .content()

        // Step 2: 구조화
        val structured = chatClient.prompt()
            .system("분석 결과를 구조화된 개요로 변환하세요.")
            .user(analysis)
            .call()
            .content()

        // Step 3: 최종 문서 생성
        val document = chatClient.prompt()
            .system("개요를 바탕으로 완전한 문서를 작성하세요.")
            .user(structured)
            .call()
            .content()

        return document
    }
}
```

이 코드를 보면 세 번의 LLM 호출이 체인처럼 연결되어 있습니다. 각 단계는 명확한 역할을 가지고 있고, 앞 단계의 결과를 받아 다음 단계로 전달합니다.

### 4.1.3 타입 안전한 체인

실제 프로젝트에서는 각 단계의 결과를 **구조화된 타입**으로 받는 것이 좋습니다. 이렇게 하면 데이터의 형태가 명확해지고, 컴파일 타임에 오류를 잡을 수 있습니다.

```kotlin
// 각 단계의 결과를 표현하는 데이터 클래스들
data class AnalysisResult(
    val mainTopic: String,
    val themes: List<String>,
    val tone: String,
    val complexity: Int  // 1-10
)

data class OutlineResult(
    val title: String,
    val sections: List<Section>
)

data class Section(
    val heading: String,
    val points: List<String>
)

data class Document(
    val title: String,
    val content: String,
    val wordCount: Int
)

@Service
class TypedChainWorkflow(
    private val chatClient: ChatClient,
    private val objectMapper: ObjectMapper
) {

    fun process(input: String): Document {
        // Step 1: 분석 (구조화된 출력)
        val analysis = chatClient.prompt()
            .system("""
                텍스트를 분석하여 다음 정보를 추출하세요:
                - mainTopic: 핵심 주제
                - themes: 주요 테마 목록 (3-5개)
                - tone: 글의 톤 (formal, casual, academic 등)
                - complexity: 복잡도 (1-10)
            """.trimIndent())
            .user(input)
            .call()
            .entity(AnalysisResult::class.java)

        // Step 2: 개요 생성
        val outline = chatClient.prompt()
            .system("분석 결과를 바탕으로 문서 개요를 작성하세요.")
            .user(objectMapper.writeValueAsString(analysis))
            .call()
            .entity(OutlineResult::class.java)

        // Step 3: 문서 생성 (분석 결과의 톤과 복잡도 반영)
        val document = chatClient.prompt()
            .system("""
                개요를 따라 완전한 문서를 작성하세요.
                - 톤: ${analysis.tone}
                - 목표 복잡도: ${analysis.complexity}/10
            """.trimIndent())
            .user(objectMapper.writeValueAsString(outline))
            .call()
            .entity(Document::class.java)

        return document
    }
}
```

> **Tip**: `entity()` 메서드는 Part 2에서 배운 Structured Output 기능입니다. AI 응답을 자동으로 지정한 클래스로 변환해줍니다.

### 4.1.4 조건부 흐름 (게이트)

항상 모든 단계를 실행할 필요는 없습니다. 조건에 따라 다른 경로를 탈 수 있습니다.

```kotlin
enum class ContentType {
    TECHNICAL, CREATIVE, BUSINESS, GENERAL
}

data class ContentClassification(
    val type: ContentType,
    val confidence: Double,
    val reason: String
)

data class QualityCheck(
    val score: Double,  // 0.0 ~ 1.0
    val feedback: String,
    val passedCriteria: List<String>,
    val failedCriteria: List<String>
)

@Service
class ConditionalChainWorkflow(
    private val chatClient: ChatClient
) {

    fun process(content: String): ProcessingResult {
        // Step 1: 콘텐츠 분류
        val classification = classifyContent(content)

        // Step 2: 분류에 따른 조건부 처리
        val processed = when (classification.type) {
            ContentType.TECHNICAL -> processTechnical(content, classification)
            ContentType.CREATIVE -> processCreative(content, classification)
            ContentType.BUSINESS -> processBusiness(content, classification)
            ContentType.GENERAL -> processGeneral(content)
        }

        // Step 3: 품질 검증 게이트
        val quality = checkQuality(processed)

        val finalContent = if (quality.score < 0.7) {
            // 품질 미달 시 개선 단계 추가
            improveQuality(processed, quality.feedback)
        } else {
            processed
        }

        return ProcessingResult(finalContent, classification, quality)
    }

    private fun classifyContent(content: String): ContentClassification {
        return chatClient.prompt()
            .system("""
                콘텐츠를 다음 중 하나로 분류하세요:
                - TECHNICAL: 기술 문서, 코드, 튜토리얼
                - CREATIVE: 창작물, 이야기, 시
                - BUSINESS: 비즈니스 문서, 보고서, 제안서
                - GENERAL: 일반적인 정보성 글

                confidence는 0.0~1.0 사이 값으로 표시하세요.
            """.trimIndent())
            .user(content)
            .call()
            .entity(ContentClassification::class.java)
    }

    private fun checkQuality(content: String): QualityCheck {
        return chatClient.prompt()
            .system("""
                콘텐츠의 품질을 평가하세요:
                - 완성도
                - 명확성
                - 구조
                - 문법

                score는 0.0~1.0 사이 값으로 종합 점수를 매기세요.
            """.trimIndent())
            .user(content)
            .call()
            .entity(QualityCheck::class.java)
    }

    private fun improveQuality(content: String, feedback: String): String {
        return chatClient.prompt()
            .system("""
                피드백을 반영하여 콘텐츠를 개선하세요.

                피드백: $feedback
            """.trimIndent())
            .user(content)
            .call()
            .content()
    }

    // 각 유형별 처리 메서드들...
    private fun processTechnical(content: String, classification: ContentClassification) =
        processWithPrompt(content, "기술 문서 스타일로 명확하고 정확하게 다시 작성하세요.")

    private fun processCreative(content: String, classification: ContentClassification) =
        processWithPrompt(content, "창의적이고 흥미로운 스타일로 다시 작성하세요.")

    private fun processBusiness(content: String, classification: ContentClassification) =
        processWithPrompt(content, "비즈니스 전문가 톤으로 다시 작성하세요.")

    private fun processGeneral(content: String) =
        processWithPrompt(content, "읽기 쉽고 이해하기 쉽게 다시 작성하세요.")

    private fun processWithPrompt(content: String, instruction: String): String {
        return chatClient.prompt()
            .system(instruction)
            .user(content)
            .call()
            .content()
    }
}
```

### 4.1.5 에러 처리 및 복구

실제 운영 환경에서는 각 단계에서 에러가 발생할 수 있습니다. 견고한 체인을 만들려면 재시도와 폴백 로직이 필요합니다.

```kotlin
data class StepResult(
    val stepName: String,
    val output: String?,
    val success: Boolean,
    val error: String? = null
)

data class ChainResult(
    val finalOutput: String?,
    val stepResults: List<StepResult>,
    val success: Boolean,
    val error: String? = null
) {
    companion object {
        fun success(output: String, steps: List<StepResult>) =
            ChainResult(output, steps, true)

        fun failed(steps: List<StepResult>, error: String) =
            ChainResult(null, steps, false, error)
    }
}

interface ChainStep {
    val name: String
    val isRequired: Boolean
    fun execute(input: String): String
}

@Service
class ResilientChainWorkflow(
    private val chatClient: ChatClient
) {
    private val maxRetries = 3

    fun process(input: String, steps: List<ChainStep>): ChainResult {
        val stepResults = mutableListOf<StepResult>()
        var currentInput = input

        for (step in steps) {
            val result = executeWithRetry(step, currentInput)
            stepResults.add(result)

            if (!result.success) {
                // 실패 시 폴백 또는 중단
                return if (step.isRequired) {
                    ChainResult.failed(stepResults, result.error ?: "Unknown error")
                } else {
                    // 선택적 단계는 스킵하고 계속 진행
                    continue
                }
            }

            currentInput = result.output!!
        }

        return ChainResult.success(currentInput, stepResults)
    }

    private fun executeWithRetry(step: ChainStep, input: String): StepResult {
        var lastError: String? = null

        repeat(maxRetries) { attempt ->
            try {
                val output = step.execute(input)
                return StepResult(step.name, output, true)
            } catch (e: Exception) {
                lastError = e.message
                if (attempt < maxRetries - 1) {
                    // 지수 백오프
                    Thread.sleep(1000L * (attempt + 1))
                }
            }
        }

        return StepResult(step.name, null, false, lastError)
    }
}
```

### 4.1.6 실습: 콘텐츠 생성 파이프라인

실제 사용할 수 있는 완전한 콘텐츠 생성 파이프라인을 만들어 봅시다.

```kotlin
// 파이프라인 각 단계의 결과 클래스들
data class TopicExpansion(
    val thesis: String,
    val subtopics: List<String>,
    val targetAudience: String,
    val uniqueAngle: String
)

data class ResearchPoints(
    val keyFacts: List<String>,
    val statistics: List<String>,
    val quotes: List<String>
)

data class DetailedOutline(
    val title: String,
    val introduction: String,
    val sections: List<OutlineSection>,
    val conclusion: String
)

data class OutlineSection(
    val heading: String,
    val keyPoints: List<String>,
    val targetWordCount: Int
)

data class Draft(
    val content: String,
    val sectionCount: Int,
    val wordCount: Int
)

data class EditedContent(
    val content: String,
    val improvements: List<String>
)

data class FinalContent(
    val content: String,
    val title: String,
    val summary: String
)

data class ContentRequest(
    val topic: String,
    val style: String = "informative",
    val requirements: List<String> = emptyList()
)

data class PipelineContext(
    var request: ContentRequest,
    var topicExpansion: TopicExpansion? = null,
    var research: ResearchPoints? = null,
    var outline: DetailedOutline? = null,
    var draft: Draft? = null,
    var edited: EditedContent? = null,
    var final: FinalContent? = null
)

data class ContentResult(
    val content: FinalContent,
    val metadata: PipelineContext
)

@Service
class ContentCreationPipeline(
    private val chatClient: ChatClient,
    private val objectMapper: ObjectMapper
) {

    fun createContent(request: ContentRequest): ContentResult {
        val context = PipelineContext(request)

        // Stage 1: 주제 확장
        val expansion = expandTopic(request.topic)
        context.topicExpansion = expansion
        println("✅ Stage 1 완료: 주제 확장")

        // Stage 2: 리서치 포인트 생성
        val research = generateResearchPoints(expansion)
        context.research = research
        println("✅ Stage 2 완료: 리서치")

        // Stage 3: 상세 개요
        val outline = createOutline(expansion, research)
        context.outline = outline
        println("✅ Stage 3 완료: 개요 작성")

        // Stage 4: 초안 작성
        val draft = writeDraft(outline)
        context.draft = draft
        println("✅ Stage 4 완료: 초안 작성 (${draft.wordCount} 단어)")

        // Stage 5: 편집 및 개선
        val edited = editAndImprove(draft, request.style)
        context.edited = edited
        println("✅ Stage 5 완료: 편집")

        // Stage 6: 최종 검토
        val finalContent = finalReview(edited, request.requirements)
        context.final = finalContent
        println("✅ Stage 6 완료: 최종본 완성!")

        return ContentResult(finalContent, context)
    }

    private fun expandTopic(topic: String): TopicExpansion {
        return chatClient.prompt()
            .system("""
                주어진 주제를 다음 요소로 확장하세요:
                1. thesis: 핵심 논제 (한 문장)
                2. subtopics: 하위 주제 (3-5개)
                3. targetAudience: 대상 독자
                4. uniqueAngle: 차별화된 관점
            """.trimIndent())
            .user("주제: $topic")
            .call()
            .entity(TopicExpansion::class.java)
    }

    private fun generateResearchPoints(expansion: TopicExpansion): ResearchPoints {
        return chatClient.prompt()
            .system("""
                주제에 대한 리서치 포인트를 생성하세요:
                - keyFacts: 핵심 사실 (5-7개)
                - statistics: 관련 통계 (3-5개)
                - quotes: 인용할 만한 문구 (2-3개)
            """.trimIndent())
            .user(objectMapper.writeValueAsString(expansion))
            .call()
            .entity(ResearchPoints::class.java)
    }

    private fun createOutline(
        expansion: TopicExpansion,
        research: ResearchPoints
    ): DetailedOutline {
        return chatClient.prompt()
            .system("""
                상세한 문서 개요를 작성하세요.
                각 섹션별로 핵심 포인트와 목표 단어 수를 포함하세요.
            """.trimIndent())
            .user("""
                주제 확장: ${objectMapper.writeValueAsString(expansion)}
                리서치: ${objectMapper.writeValueAsString(research)}
            """.trimIndent())
            .call()
            .entity(DetailedOutline::class.java)
    }

    private fun writeDraft(outline: DetailedOutline): Draft {
        val contentParts = mutableListOf<String>()

        // 도입부
        val intro = chatClient.prompt()
            .system("문서의 도입부를 작성하세요. 독자의 관심을 끌어야 합니다.")
            .user("제목: ${outline.title}\n개요: ${outline.introduction}")
            .call()
            .content()
        contentParts.add(intro)

        // 각 섹션 작성
        for (section in outline.sections) {
            val sectionContent = chatClient.prompt()
                .system("""
                    다음 섹션을 작성하세요.
                    - 핵심 포인트를 모두 포함하세요
                    - 목표: ${section.targetWordCount} 단어 내외
                """.trimIndent())
                .user("""
                    제목: ${section.heading}
                    포인트: ${section.keyPoints.joinToString("\n- ")}
                """.trimIndent())
                .call()
                .content()

            contentParts.add("\n\n## ${section.heading}\n\n$sectionContent")
        }

        // 결론
        val conclusion = chatClient.prompt()
            .system("문서의 결론을 작성하세요. 핵심 내용을 요약하고 행동 촉구를 포함하세요.")
            .user("개요: ${outline.conclusion}")
            .call()
            .content()
        contentParts.add("\n\n## 결론\n\n$conclusion")

        val fullContent = contentParts.joinToString("")
        val wordCount = fullContent.split("\\s+".toRegex()).size

        return Draft(fullContent, outline.sections.size, wordCount)
    }

    private fun editAndImprove(draft: Draft, style: String): EditedContent {
        return chatClient.prompt()
            .system("""
                초안을 편집하고 개선하세요:
                - 문체: $style
                - 문법 및 맞춤법 교정
                - 가독성 향상
                - 흐름 개선

                improvements에 주요 변경사항을 기록하세요.
            """.trimIndent())
            .user(draft.content)
            .call()
            .entity(EditedContent::class.java)
    }

    private fun finalReview(
        edited: EditedContent,
        requirements: List<String>
    ): FinalContent {
        val reqText = if (requirements.isNotEmpty()) {
            "요구사항:\n" + requirements.joinToString("\n") { "- $it" }
        } else {
            "특별한 요구사항 없음"
        }

        return chatClient.prompt()
            .system("""
                최종 검토를 수행하세요:
                1. 요구사항 충족 여부 확인
                2. 제목 확정
                3. 요약문 작성 (2-3문장)

                $reqText
            """.trimIndent())
            .user(edited.content)
            .call()
            .entity(FinalContent::class.java)
    }
}
```

#### 사용 예시

```kotlin
@RestController
@RequestMapping("/api/content")
class ContentController(
    private val pipeline: ContentCreationPipeline
) {

    @PostMapping("/generate")
    fun generateContent(@RequestBody request: ContentRequest): ContentResult {
        return pipeline.createContent(request)
    }
}

// 호출 예시
// POST /api/content/generate
// {
//   "topic": "Spring AI로 시작하는 AI 애플리케이션 개발",
//   "style": "tutorial",
//   "requirements": ["초보자도 이해할 수 있게", "실제 코드 예시 포함"]
// }
```

---

## Module 4.2: Parallelization Workflow (병렬화 워크플로우)

### 4.2.1 병렬화 패턴 개요

체인 워크플로우가 **순차적**이라면, 병렬화 워크플로우는 **동시에** 여러 작업을 처리합니다. 서로 독립적인 작업들이라면 굳이 기다릴 필요가 없습니다.

#### Sectioning (분할) 패턴

하나의 입력을 여러 관점에서 동시에 분석합니다.

```
         ┌──→ [Task A] ──┐
Input ───┼──→ [Task B] ──┼──→ Aggregate → Output
         └──→ [Task C] ──┘
```

#### Voting (투표) 패턴

같은 질문을 여러 번 물어보고 다수결로 결정합니다.

```
         ┌──→ [Model 1] ──┐
Input ───┼──→ [Model 2] ──┼──→ Vote/Consensus → Output
         └──→ [Model 3] ──┘
```

### 4.2.2 Coroutine 기반 구현 (Kotlin)

Kotlin의 **코루틴**을 활용하면 비동기 병렬 처리를 우아하게 작성할 수 있습니다.

```kotlin
// 분석 결과 데이터 클래스들
data class SentimentResult(
    val sentiment: String,  // POSITIVE, NEGATIVE, NEUTRAL
    val confidence: Double,
    val emotions: List<String>
)

data class KeywordsResult(
    val keywords: List<String>,
    val phrases: List<String>
)

data class Summary(
    val title: String,
    val summary: String,
    val keyPoints: List<String>
)

data class Entity(
    val name: String,
    val type: String,  // PERSON, ORGANIZATION, LOCATION, DATE
    val mentions: Int
)

data class ParallelAnalysisResult(
    val sentiment: SentimentResult,
    val keywords: KeywordsResult,
    val summary: Summary,
    val entities: List<Entity>,
    val processingTimeMs: Long
)

@Service
class ParallelWorkflow(
    private val chatClient: ChatClient
) {

    suspend fun analyzeDocument(document: String): ParallelAnalysisResult {
        val startTime = System.currentTimeMillis()

        // 병렬 작업 시작
        return coroutineScope {
            val sentimentDeferred = async { analyzeSentiment(document) }
            val keywordsDeferred = async { extractKeywords(document) }
            val summaryDeferred = async { summarize(document) }
            val entitiesDeferred = async { extractEntities(document) }

            // 모든 결과 대기 (동시에 실행됨)
            val sentiment = sentimentDeferred.await()
            val keywords = keywordsDeferred.await()
            val summary = summaryDeferred.await()
            val entities = entitiesDeferred.await()

            val processingTime = System.currentTimeMillis() - startTime

            ParallelAnalysisResult(
                sentiment = sentiment,
                keywords = keywords,
                summary = summary,
                entities = entities,
                processingTimeMs = processingTime
            )
        }
    }

    private fun analyzeSentiment(document: String): SentimentResult {
        return chatClient.prompt()
            .system("""
                문서의 감성을 분석하세요:
                - sentiment: POSITIVE, NEGATIVE, NEUTRAL 중 하나
                - confidence: 확신도 (0.0~1.0)
                - emotions: 감지된 감정들 (joy, sadness, anger, fear 등)
            """.trimIndent())
            .user(document)
            .call()
            .entity(SentimentResult::class.java)
    }

    private fun extractKeywords(document: String): KeywordsResult {
        return chatClient.prompt()
            .system("""
                문서에서 키워드를 추출하세요:
                - keywords: 단일 키워드 (10개 이내)
                - phrases: 핵심 구문 (5개 이내)
            """.trimIndent())
            .user(document)
            .call()
            .entity(KeywordsResult::class.java)
    }

    private fun summarize(document: String): Summary {
        return chatClient.prompt()
            .system("""
                문서를 요약하세요:
                - title: 제목 (10단어 이내)
                - summary: 요약문 (2-3문장)
                - keyPoints: 핵심 포인트 (3-5개)
            """.trimIndent())
            .user(document)
            .call()
            .entity(Summary::class.java)
    }

    private fun extractEntities(document: String): List<Entity> {
        data class EntityList(val entities: List<Entity>)

        return chatClient.prompt()
            .system("""
                문서에서 개체명을 추출하세요:
                - 인물 (PERSON)
                - 조직 (ORGANIZATION)
                - 장소 (LOCATION)
                - 날짜 (DATE)
            """.trimIndent())
            .user(document)
            .call()
            .entity(EntityList::class.java)
            .entities
    }
}
```

### 4.2.3 Reactor 기반 구현 (WebFlux)

Spring WebFlux를 사용한다면 **Reactor**의 `Mono`와 `Flux`를 활용할 수 있습니다.

```kotlin
@Service
class ReactiveParallelWorkflow(
    private val chatClient: ChatClient
) {

    fun analyzeReactive(document: String): Mono<AnalysisResult> {
        val sentiment = Mono.fromCallable { analyzeSentiment(document) }
            .subscribeOn(Schedulers.boundedElastic())

        val keywords = Mono.fromCallable { extractKeywords(document) }
            .subscribeOn(Schedulers.boundedElastic())

        val summary = Mono.fromCallable { summarize(document) }
            .subscribeOn(Schedulers.boundedElastic())

        return Mono.zip(sentiment, keywords, summary)
            .map { tuple ->
                AnalysisResult(
                    sentiment = tuple.t1,
                    keywords = tuple.t2,
                    summary = tuple.t3
                )
            }
    }

    // 여러 문서 배치 처리
    fun analyzeBatch(documents: List<String>): Flux<DocumentAnalysis> {
        return Flux.fromIterable(documents)
            .flatMap(
                { doc -> analyzeReactive(doc).map { DocumentAnalysis(doc, it) } },
                5  // 동시성 제한: 최대 5개 동시 처리
            )
            .onErrorContinue { e, doc ->
                println("분석 실패: $doc - ${e.message}")
            }
    }
}
```

### 4.2.4 Voting 패턴

같은 질문을 여러 번 물어보고 **다수결**로 결정하는 패턴입니다. AI의 응답이 확률적이기 때문에, 여러 번 물어서 가장 많이 나온 답을 선택하면 신뢰도가 높아집니다.

```kotlin
data class VotingResult(
    val winner: String,
    val confidence: Double,
    val votes: Map<String, Int>,
    val totalVotes: Int
)

@Service
class VotingWorkflow(
    private val chatClient: ChatClient
) {

    suspend fun classifyWithVoting(
        text: String,
        samples: Int = 5
    ): VotingResult = coroutineScope {

        // 여러 번 동시에 분류 요청
        val deferredResults = (1..samples).map {
            async {
                chatClient.prompt()
                    .system("""
                        텍스트를 정확히 하나의 카테고리로 분류하세요:
                        POSITIVE, NEGATIVE, NEUTRAL

                        카테고리 이름만 응답하세요.
                    """.trimIndent())
                    .options(ChatOptionsBuilder.builder()
                        .withTemperature(0.7f)  // 약간의 변동성 부여
                        .build())
                    .user(text)
                    .call()
                    .content()
                    .trim()
                    .uppercase()
            }
        }

        // 결과 집계
        val results = deferredResults.awaitAll()
        val votes = results.groupingBy { it }.eachCount()

        // 최다 득표 선택
        val winner = votes.maxByOrNull { it.value }?.key ?: "UNKNOWN"
        val confidence = votes[winner]?.toDouble()?.div(samples) ?: 0.0

        VotingResult(
            winner = winner,
            confidence = confidence,
            votes = votes,
            totalVotes = samples
        )
    }
}
```

### 4.2.5 결과 집계 전략

병렬 작업의 결과를 합치는 다양한 전략이 있습니다.

```kotlin
// 집계 전략 인터페이스
interface AggregationStrategy<T> {
    fun aggregate(results: List<T>): T?
}

// 다수결 전략
class MajorityVoteStrategy : AggregationStrategy<String> {
    override fun aggregate(results: List<String>): String? {
        return results
            .groupingBy { it }
            .eachCount()
            .maxByOrNull { it.value }
            ?.key
    }
}

// 평균 전략 (숫자용)
class AverageStrategy : AggregationStrategy<Double> {
    override fun aggregate(results: List<Double>): Double? {
        return if (results.isEmpty()) null else results.average()
    }
}

// 최고 신뢰도 전략
data class ScoredResult(val value: String, val confidence: Double)

class HighestConfidenceStrategy : AggregationStrategy<ScoredResult> {
    override fun aggregate(results: List<ScoredResult>): ScoredResult? {
        return results.maxByOrNull { it.confidence }
    }
}

// 만장일치 전략 (모두 같아야 함)
class ConsensusStrategy : AggregationStrategy<String> {
    override fun aggregate(results: List<String>): String? {
        val unique = results.toSet()
        return if (unique.size == 1) results.first() else null
    }
}

// 가중 평균 전략
data class WeightedResult(val value: Double, val weight: Double)

class WeightedAverageStrategy : AggregationStrategy<WeightedResult> {
    override fun aggregate(results: List<WeightedResult>): WeightedResult? {
        if (results.isEmpty()) return null

        val totalWeight = results.sumOf { it.weight }
        val weightedSum = results.sumOf { it.value * it.weight }

        return WeightedResult(
            value = weightedSum / totalWeight,
            weight = totalWeight
        )
    }
}
```

### 4.2.6 실습: 다중 관점 문서 분석기

하나의 문서를 여러 전문가의 관점에서 동시에 분석하는 시스템을 만들어 봅시다.

```kotlin
// 각 관점별 분석 결과
data class TechnicalAnalysis(
    val architectureConsiderations: List<String>,
    val technologyImplications: List<String>,
    val scalabilityConcerns: List<String>,
    val technicalDebtPotential: String
)

data class BusinessAnalysis(
    val marketOpportunities: List<String>,
    val competitiveAdvantages: List<String>,
    val revenueImplications: String,
    val resourceRequirements: String
)

data class LegalAnalysis(
    val complianceIssues: List<String>,
    val riskFactors: List<String>,
    val recommendations: List<String>
)

data class RiskAnalysis(
    val identifiedRisks: List<Risk>,
    val overallRiskLevel: String,  // LOW, MEDIUM, HIGH, CRITICAL
    val mitigationStrategies: List<String>
)

data class Risk(
    val description: String,
    val likelihood: String,
    val impact: String
)

data class ComprehensiveAnalysis(
    val executiveSummary: String,
    val keyAgreements: List<String>,
    val conflictingViewpoints: List<String>,
    val priorityRecommendations: List<String>,
    val actionItems: List<String>
)

data class MultiPerspectiveResult(
    val technical: TechnicalAnalysis,
    val business: BusinessAnalysis,
    val legal: LegalAnalysis,
    val risk: RiskAnalysis,
    val synthesis: ComprehensiveAnalysis,
    val processingTimeMs: Long
)

@Service
class MultiPerspectiveAnalyzer(
    private val chatClient: ChatClient,
    private val objectMapper: ObjectMapper
) {

    suspend fun analyze(document: String): MultiPerspectiveResult {
        val startTime = System.currentTimeMillis()

        // 병렬 분석 실행
        val (tech, biz, legal, risk) = coroutineScope {
            val techDeferred = async { analyzeTechnical(document) }
            val bizDeferred = async { analyzeBusiness(document) }
            val legalDeferred = async { analyzeLegal(document) }
            val riskDeferred = async { analyzeRisk(document) }

            listOf(
                techDeferred.await(),
                bizDeferred.await(),
                legalDeferred.await(),
                riskDeferred.await()
            )
        }

        // 종합 보고서 생성 (분석 결과를 기반으로)
        val synthesis = synthesize(
            tech as TechnicalAnalysis,
            biz as BusinessAnalysis,
            legal as LegalAnalysis,
            risk as RiskAnalysis
        )

        val processingTime = System.currentTimeMillis() - startTime

        return MultiPerspectiveResult(
            technical = tech,
            business = biz,
            legal = legal,
            risk = risk,
            synthesis = synthesis,
            processingTimeMs = processingTime
        )
    }

    private fun analyzeTechnical(document: String): TechnicalAnalysis {
        return chatClient.prompt()
            .system("""
                당신은 시니어 기술 아키텍트입니다.
                기술적 관점에서 문서를 분석하세요:
                - 아키텍처 고려사항
                - 기술 스택 시사점
                - 확장성 우려
                - 기술 부채 가능성
            """.trimIndent())
            .user(document)
            .call()
            .entity(TechnicalAnalysis::class.java)
    }

    private fun analyzeBusiness(document: String): BusinessAnalysis {
        return chatClient.prompt()
            .system("""
                당신은 비즈니스 전략 컨설턴트입니다.
                비즈니스 관점에서 문서를 분석하세요:
                - 시장 기회
                - 경쟁 우위
                - 수익 영향
                - 필요 리소스
            """.trimIndent())
            .user(document)
            .call()
            .entity(BusinessAnalysis::class.java)
    }

    private fun analyzeLegal(document: String): LegalAnalysis {
        return chatClient.prompt()
            .system("""
                당신은 법률 자문가입니다.
                법적 관점에서 문서를 분석하세요:
                - 규정 준수 이슈
                - 리스크 요소
                - 권고사항
            """.trimIndent())
            .user(document)
            .call()
            .entity(LegalAnalysis::class.java)
    }

    private fun analyzeRisk(document: String): RiskAnalysis {
        return chatClient.prompt()
            .system("""
                당신은 리스크 관리 전문가입니다.
                리스크 관점에서 문서를 분석하세요:
                - 식별된 리스크 (각각의 가능성과 영향도 포함)
                - 전체 리스크 수준
                - 완화 전략
            """.trimIndent())
            .user(document)
            .call()
            .entity(RiskAnalysis::class.java)
    }

    private fun synthesize(
        tech: TechnicalAnalysis,
        biz: BusinessAnalysis,
        legal: LegalAnalysis,
        risk: RiskAnalysis
    ): ComprehensiveAnalysis {
        return chatClient.prompt()
            .system("""
                다양한 관점의 분석을 종합하여 경영진 요약을 작성하세요.

                포함할 내용:
                - 핵심 요약 (2-3문장)
                - 관점 간 일치 사항
                - 상충되는 의견과 해결 방안
                - 우선순위 권고사항
                - 구체적 액션 아이템
            """.trimIndent())
            .user("""
                기술 분석: ${objectMapper.writeValueAsString(tech)}
                비즈니스 분석: ${objectMapper.writeValueAsString(biz)}
                법률 분석: ${objectMapper.writeValueAsString(legal)}
                리스크 분석: ${objectMapper.writeValueAsString(risk)}
            """.trimIndent())
            .call()
            .entity(ComprehensiveAnalysis::class.java)
    }
}
```

---

## Module 4.3: Routing Workflow (라우팅 워크플로우)

### 4.3.1 라우팅 개념

**라우팅 워크플로우**는 입력을 분류하고, 분류 결과에 따라 적절한 처리기로 보내는 패턴입니다. 고객 문의를 담당 부서로 연결하는 콜센터와 비슷합니다.

```
              ┌──→ [Handler A]
Input → [Classifier] ──→ [Handler B] → Output
              └──→ [Handler C]
```

#### 실제 사용 사례

- **고객 지원**: 문의 유형별 전문 상담사 연결
- **콘텐츠 처리**: 콘텐츠 유형별 다른 처리 로직
- **모델 선택**: 복잡도에 따라 다른 AI 모델 사용

### 4.3.2 기본 라우팅 구현

```kotlin
// 분류 결과
data class Classification(
    val category: String,
    val urgency: Urgency,
    val sentiment: Sentiment,
    val reasoning: String
)

enum class Urgency { LOW, MEDIUM, HIGH, CRITICAL }
enum class Sentiment { POSITIVE, NEUTRAL, NEGATIVE }

// 핸들러 인터페이스
interface Handler {
    fun handle(input: String, classification: Classification): String
    fun canHandle(category: String): Boolean
}

data class RoutingResult(
    val classification: Classification,
    val response: String,
    val handlerUsed: String
)

@Service
class RoutingWorkflow(
    private val chatClient: ChatClient,
    private val handlers: Map<String, Handler>
) {

    fun route(input: String): RoutingResult {
        // Step 1: 분류
        val classification = classify(input)

        // Step 2: 핸들러 선택
        val handler = handlers[classification.category]
            ?: handlers["default"]
            ?: throw IllegalStateException("No handler available")

        // Step 3: 처리
        val result = handler.handle(input, classification)

        return RoutingResult(classification, result, classification.category)
    }

    private fun classify(input: String): Classification {
        return chatClient.prompt()
            .system("""
                사용자 입력을 다음 카테고리 중 하나로 분류하세요:

                카테고리:
                - TECHNICAL_SUPPORT: 기술적 문제, 버그, 에러
                - BILLING: 결제, 구독, 환불 문의
                - GENERAL_INQUIRY: 제품 정보, 기능 문의
                - FEEDBACK: 제안, 불만, 칭찬

                긴급도 평가:
                - LOW: 일반 문의
                - MEDIUM: 업무에 불편함
                - HIGH: 서비스 사용 불가
                - CRITICAL: 데이터 손실 위험

                감성 평가:
                - POSITIVE, NEUTRAL, NEGATIVE
            """.trimIndent())
            .user(input)
            .call()
            .entity(Classification::class.java)
    }
}
```

### 4.3.3 전문화된 핸들러

각 카테고리별로 전문화된 핸들러를 구현합니다.

```kotlin
@Component
class TechnicalSupportHandler(
    private val chatClient: ChatClient
) : Handler {

    override fun handle(input: String, classification: Classification): String {
        return chatClient.prompt()
            .system("""
                당신은 기술 지원 전문가입니다.

                응답 지침:
                1. 문제를 명확히 이해했음을 확인
                2. 단계별 해결 방법 제시
                3. 추가 도움이 필요한 경우 안내

                긴급도: ${classification.urgency}
            """.trimIndent())
            .user(input)
            .call()
            .content()
    }

    override fun canHandle(category: String) = category == "TECHNICAL_SUPPORT"
}

@Component
class BillingHandler(
    private val chatClient: ChatClient
) : Handler {

    override fun handle(input: String, classification: Classification): String {
        return chatClient.prompt()
            .system("""
                당신은 결제 및 구독 담당 상담사입니다.

                응답 지침:
                1. 정책을 명확히 설명
                2. 가능한 옵션 제시
                3. 필요 시 담당 부서 연결 안내

                고객 감성: ${classification.sentiment}
                (부정적인 경우 더 공감하는 태도로)
            """.trimIndent())
            .user(input)
            .call()
            .content()
    }

    override fun canHandle(category: String) = category == "BILLING"
}

@Component
class DefaultHandler(
    private val chatClient: ChatClient
) : Handler {

    override fun handle(input: String, classification: Classification): String {
        return chatClient.prompt()
            .system("""
                친절하고 도움이 되는 고객 상담사로서 응답하세요.
                분류할 수 없는 문의에 대해 일반적인 안내를 제공합니다.
            """.trimIndent())
            .user(input)
            .call()
            .content()
    }

    override fun canHandle(category: String) = true
}
```

### 4.3.4 핸들러 자동 등록

Spring의 의존성 주입을 활용하면 핸들러를 자동으로 등록할 수 있습니다.

```kotlin
@Configuration
class RoutingConfiguration {

    @Bean
    fun handlerMap(handlers: List<Handler>): Map<String, Handler> {
        val map = mutableMapOf<String, Handler>()

        handlers.forEach { handler ->
            when (handler) {
                is TechnicalSupportHandler -> map["TECHNICAL_SUPPORT"] = handler
                is BillingHandler -> map["BILLING"] = handler
                is GeneralInquiryHandler -> map["GENERAL_INQUIRY"] = handler
                is FeedbackHandler -> map["FEEDBACK"] = handler
                is DefaultHandler -> map["default"] = handler
            }
        }

        return map
    }
}
```

### 4.3.5 멀티레벨 라우팅

복잡한 시나리오에서는 **계층적 라우팅**이 필요할 수 있습니다.

```kotlin
data class Level1Classification(
    val domain: String,  // SALES, SUPPORT, ADMIN
    val confidence: Double
)

data class Level2Classification(
    val subCategory: String,
    val specificIssue: String,
    val needsDetailedClassification: Boolean
)

data class Level3Classification(
    val detailedType: String,
    val suggestedHandler: String
)

@Service
class HierarchicalRouter(
    private val chatClient: ChatClient,
    private val handlers: Map<String, Map<String, Handler>>
) {

    fun route(input: String): RoutingResult {
        // Level 1: 대분류
        val l1 = classifyLevel1(input)
        println("L1 분류: ${l1.domain}")

        // Level 2: 중분류
        val l2 = classifyLevel2(input, l1)
        println("L2 분류: ${l2.subCategory}")

        // Level 3: 소분류 (필요시)
        val l3 = if (l2.needsDetailedClassification) {
            classifyLevel3(input, l2).also {
                println("L3 분류: ${it.detailedType}")
            }
        } else null

        // 최종 핸들러 선택
        val handler = selectHandler(l1, l2, l3)

        return handler.process(input)
    }

    private fun selectHandler(
        l1: Level1Classification,
        l2: Level2Classification,
        l3: Level3Classification?
    ): Handler {
        val domainHandlers = handlers[l1.domain] ?: handlers["default"]!!

        return if (l3 != null) {
            domainHandlers[l3.detailedType]
                ?: domainHandlers[l2.subCategory]
                ?: domainHandlers["default"]!!
        } else {
            domainHandlers[l2.subCategory]
                ?: domainHandlers["default"]!!
        }
    }
}
```

### 4.3.6 폴백 전략

핸들러 실패 시 대안을 제공하는 **폴백 전략**은 안정적인 서비스를 위해 필수적입니다.

```kotlin
@Service
class ResilientRoutingWorkflow(
    private val chatClient: ChatClient,
    private val handlers: Map<String, Handler>,
    private val defaultHandler: Handler
) {
    private val logger = LoggerFactory.getLogger(javaClass)

    fun route(input: String): String {
        val classification = classify(input)

        // 1차: 전문 핸들러 시도
        handlers[classification.category]?.let { handler ->
            try {
                return handler.handle(input, classification)
            } catch (e: Exception) {
                logger.warn("Primary handler failed: ${e.message}")
            }
        }

        // 2차: 유사 카테고리 핸들러
        findSimilarHandler(classification)?.let { handler ->
            try {
                return handler.handle(input, classification)
            } catch (e: Exception) {
                logger.warn("Similar handler failed: ${e.message}")
            }
        }

        // 3차: 기본 핸들러
        return defaultHandler.handle(input, classification)
    }

    private fun findSimilarHandler(classification: Classification): Handler? {
        // 카테고리 유사도 매핑
        val similarCategories = mapOf(
            "TECHNICAL_SUPPORT" to listOf("GENERAL_INQUIRY"),
            "BILLING" to listOf("GENERAL_INQUIRY"),
            "FEEDBACK" to listOf("GENERAL_INQUIRY")
        )

        val similar = similarCategories[classification.category] ?: emptyList()

        return similar
            .mapNotNull { handlers[it] }
            .firstOrNull()
    }
}
```

### 4.3.7 실습: 고객 문의 자동 분류 시스템

실제 고객 지원 시스템에서 사용할 수 있는 완전한 라우팅 시스템을 만들어 봅시다.

```kotlin
// 고객 컨텍스트
data class CustomerContext(
    val customerId: String,
    val accountType: String,  // FREE, PREMIUM, ENTERPRISE
    val ticketCount: Int,
    val lastInteraction: String
)

// 문의 분석 결과
data class InquiryAnalysis(
    val category: SupportCategory,
    val urgency: Urgency,
    val sentiment: Sentiment,
    val specificIssueType: String,
    val requiredInformation: List<String>,
    val suggestedApproach: String
)

enum class SupportCategory {
    BILLING, TECHNICAL, SHIPPING, RETURNS, GENERAL
}

// 지원 에이전트 인터페이스
interface SupportAgent {
    fun generateResponse(
        message: String,
        analysis: InquiryAnalysis,
        context: CustomerContext
    ): String
}

// 품질 검증
data class QualityCheck(
    val passed: Boolean,
    val score: Double,
    val feedback: String?
)

// 최종 응답
data class SupportResponse(
    val response: String,
    val category: SupportCategory,
    val urgency: Urgency,
    val confidence: Double,
    val escalated: Boolean = false
)

@Service
class CustomerSupportRouter(
    private val chatClient: ChatClient,
    private val agents: Map<SupportCategory, SupportAgent>
) {
    private val logger = LoggerFactory.getLogger(javaClass)

    fun handleInquiry(
        customerMessage: String,
        context: CustomerContext
    ): SupportResponse {

        // 1. 인텐트 분석
        val analysis = analyzeInquiry(customerMessage, context)
        logger.info("문의 분석 완료: ${analysis.category}, 긴급도: ${analysis.urgency}")

        // 2. 긴급도 평가 - CRITICAL은 인간 상담사에게 에스컬레이션
        if (analysis.urgency == Urgency.CRITICAL) {
            return escalateToHuman(customerMessage, analysis)
        }

        // 3. 적절한 에이전트 라우팅
        val agent = selectAgent(analysis)

        // 4. 응답 생성
        var response = agent.generateResponse(customerMessage, analysis, context)

        // 5. 응답 품질 검증
        val quality = validateResponse(response, analysis)
        if (!quality.passed && quality.feedback != null) {
            response = improveResponse(response, quality.feedback)
        }

        return SupportResponse(
            response = response,
            category = analysis.category,
            urgency = analysis.urgency,
            confidence = quality.score
        )
    }

    private fun analyzeInquiry(
        message: String,
        context: CustomerContext
    ): InquiryAnalysis {
        return chatClient.prompt()
            .system("""
                고객 지원 문의를 분석하세요.

                고객 정보:
                - 계정 유형: ${context.accountType}
                - 이전 티켓 수: ${context.ticketCount}
                - 마지막 연락: ${context.lastInteraction}

                분류 카테고리: BILLING, TECHNICAL, SHIPPING, RETURNS, GENERAL
                긴급도: LOW, MEDIUM, HIGH, CRITICAL
                감성: POSITIVE, NEUTRAL, NEGATIVE

                또한 다음을 식별하세요:
                - specificIssueType: 구체적인 이슈 유형
                - requiredInformation: 해결에 필요한 정보
                - suggestedApproach: 추천 해결 접근법
            """.trimIndent())
            .user(message)
            .call()
            .entity(InquiryAnalysis::class.java)
    }

    private fun selectAgent(analysis: InquiryAnalysis): SupportAgent {
        return agents[analysis.category]
            ?: agents[SupportCategory.GENERAL]
            ?: throw IllegalStateException("No agent available")
    }

    private fun validateResponse(
        response: String,
        analysis: InquiryAnalysis
    ): QualityCheck {
        return chatClient.prompt()
            .system("""
                응답의 품질을 평가하세요:
                - 고객 문의에 적절히 답변했는가?
                - 톤이 적절한가?
                - 명확하고 실행 가능한가?

                score: 0.0~1.0
                passed: score >= 0.7
            """.trimIndent())
            .user("""
                분석: ${analysis}
                응답: $response
            """.trimIndent())
            .call()
            .entity(QualityCheck::class.java)
    }

    private fun improveResponse(response: String, feedback: String): String {
        return chatClient.prompt()
            .system("""
                피드백을 반영하여 응답을 개선하세요.
                피드백: $feedback
            """.trimIndent())
            .user(response)
            .call()
            .content()
    }

    private fun escalateToHuman(
        message: String,
        analysis: InquiryAnalysis
    ): SupportResponse {
        return SupportResponse(
            response = """
                고객님의 문의가 긴급 처리가 필요한 것으로 확인되었습니다.

                전문 상담사가 곧 연락드릴 예정입니다.
                예상 대기 시간: 5분 이내

                긴급한 경우 직통 전화 1588-0000으로 연락 주시기 바랍니다.
            """.trimIndent(),
            category = analysis.category,
            urgency = analysis.urgency,
            confidence = 1.0,
            escalated = true
        )
    }
}
```

---

## Module 4.4: Orchestrator-Workers (오케스트레이터-워커)

### 4.4.1 패턴 개요

**오케스트레이터-워커** 패턴은 복잡한 작업을 동적으로 분해하고 전문화된 워커에게 분배하는 패턴입니다. 오케스트레이터가 **지휘자** 역할을, 워커들이 **연주자** 역할을 합니다.

```
                    ┌──→ [Worker 1] ──┐
[Input] → [Orchestrator] ──→ [Worker 2] ──→ [Orchestrator] → [Output]
                    └──→ [Worker 3] ──┘
```

#### 특징

- **동적 작업 분해**: 오케스트레이터가 상황에 맞게 작업을 나눔
- **전문화**: 각 워커는 특정 유형의 작업에 특화
- **적응적**: 중간 결과에 따라 계획 수정 가능

### 4.4.2 오케스트레이터 구현

```kotlin
// 작업 계획
data class TaskPlan(
    val taskId: String,
    val summary: String,
    val subTasks: List<SubTask>
)

data class SubTask(
    val id: String,
    val description: String,
    val workerType: WorkerType,
    val dependencies: List<String>,  // 의존하는 subTask ID들
    val priority: Int  // 1이 가장 높음
)

enum class WorkerType {
    RESEARCHER, WRITER, ANALYST, CODER, REVIEWER
}

// 워커 결과
data class WorkerResult(
    val taskId: String,
    val output: String,
    val success: Boolean,
    val requiresReplanning: Boolean = false,
    val metadata: Map<String, Any> = emptyMap()
)

// 최종 결과
data class OrchestratorResult(
    val finalOutput: String,
    val plan: TaskPlan,
    val workerResults: Map<String, WorkerResult>,
    val iterations: Int
)

@Service
class OrchestratorWorkflow(
    private val chatClient: ChatClient,
    private val workers: Map<WorkerType, Worker>
) {

    suspend fun execute(task: String): OrchestratorResult {
        // 1. 작업 분해
        var plan = planTasks(task)
        println("📋 작업 계획 수립: ${plan.subTasks.size}개의 하위 작업")

        val results = mutableMapOf<String, WorkerResult>()
        var iterations = 0

        // 2. 워커 실행 (의존성 순서대로)
        while (results.size < plan.subTasks.size) {
            iterations++

            // 실행 가능한 작업 찾기
            val readyTasks = plan.subTasks.filter { subTask ->
                // 아직 실행 안 됨 + 의존성 모두 완료
                !results.containsKey(subTask.id) &&
                subTask.dependencies.all { results.containsKey(it) }
            }

            if (readyTasks.isEmpty()) {
                throw IllegalStateException("순환 의존성 또는 막힌 작업 발견")
            }

            // 병렬 실행
            coroutineScope {
                readyTasks.map { subTask ->
                    async {
                        val worker = workers[subTask.workerType]
                            ?: throw IllegalStateException("Worker not found: ${subTask.workerType}")

                        // 의존 작업 결과를 컨텍스트로 전달
                        val dependencyResults = subTask.dependencies
                            .associateWith { results[it]!! }

                        val result = worker.execute(subTask, dependencyResults)

                        println("✅ ${subTask.id} 완료 (${subTask.workerType})")

                        subTask.id to result
                    }
                }.awaitAll().forEach { (id, result) ->
                    results[id] = result

                    // 재계획 필요 여부 확인
                    if (result.requiresReplanning) {
                        plan = replan(plan, results)
                    }
                }
            }
        }

        // 3. 결과 통합
        val finalOutput = synthesizeResults(task, plan, results)

        return OrchestratorResult(finalOutput, plan, results, iterations)
    }

    private fun planTasks(task: String): TaskPlan {
        return chatClient.prompt()
            .system("""
                당신은 작업 오케스트레이터입니다.
                작업을 분석하고 하위 작업으로 분해하세요.

                각 하위 작업에 대해 지정:
                - id: 고유 식별자 (예: "task-1")
                - description: 수행할 작업 설명
                - workerType: RESEARCHER, WRITER, ANALYST, CODER, REVIEWER 중 하나
                - dependencies: 이 작업이 의존하는 다른 작업 ID 목록
                - priority: 1-5 (1이 가장 높음)

                가능한 병렬 실행을 최적화하세요.
            """.trimIndent())
            .user(task)
            .call()
            .entity(TaskPlan::class.java)
    }

    private fun replan(
        currentPlan: TaskPlan,
        completedResults: Map<String, WorkerResult>
    ): TaskPlan {
        return chatClient.prompt()
            .system("""
                현재 진행 상황을 보고 계획을 수정하세요.
                완료된 작업은 유지하고, 남은 작업을 조정하세요.
            """.trimIndent())
            .user("""
                현재 계획: $currentPlan
                완료된 결과: $completedResults
            """.trimIndent())
            .call()
            .entity(TaskPlan::class.java)
    }

    private fun synthesizeResults(
        originalTask: String,
        plan: TaskPlan,
        results: Map<String, WorkerResult>
    ): String {
        return chatClient.prompt()
            .system("""
                모든 워커의 결과를 통합하여 최종 출력을 생성하세요.
                일관성 있고 완전한 결과물을 만드세요.
            """.trimIndent())
            .user("""
                원본 작업: $originalTask
                계획: $plan
                결과들: $results
            """.trimIndent())
            .call()
            .content()
    }
}
```

### 4.4.3 전문화된 워커

각 워커는 특정 유형의 작업에 특화됩니다.

```kotlin
interface Worker {
    val type: WorkerType
    fun execute(task: SubTask, dependencyResults: Map<String, WorkerResult>): WorkerResult
}

@Component
class ResearchWorker(
    private val chatClient: ChatClient
) : Worker {

    override val type = WorkerType.RESEARCHER

    override fun execute(
        task: SubTask,
        dependencyResults: Map<String, WorkerResult>
    ): WorkerResult {
        val context = dependencyResults.values
            .joinToString("\n") { it.output }

        val output = chatClient.prompt()
            .system("""
                당신은 리서치 전문가입니다.
                주어진 주제에 대해 철저히 조사하세요.

                제공할 내용:
                - 핵심 발견사항 (글머리 기호)
                - 출처/참고자료
                - 신뢰도
                - 추가 조사 필요 영역

                ${if (context.isNotEmpty()) "이전 작업 컨텍스트:\n$context" else ""}
            """.trimIndent())
            .user(task.description)
            .call()
            .content()

        return WorkerResult(
            taskId = task.id,
            output = output,
            success = true
        )
    }
}

@Component
class CoderWorker(
    private val chatClient: ChatClient
) : Worker {

    override val type = WorkerType.CODER

    override fun execute(
        task: SubTask,
        dependencyResults: Map<String, WorkerResult>
    ): WorkerResult {
        val context = dependencyResults.values
            .joinToString("\n") { it.output }

        val output = chatClient.prompt()
            .system("""
                당신은 숙련된 프로그래머입니다.
                깔끔하고 효율적이며 문서화된 코드를 작성하세요.

                포함할 내용:
                - 구현 코드
                - 단위 테스트
                - 문서/주석
                - 에러 처리

                ${if (context.isNotEmpty()) "이전 작업 컨텍스트:\n$context" else ""}
            """.trimIndent())
            .user(task.description)
            .call()
            .content()

        return WorkerResult(
            taskId = task.id,
            output = output,
            success = true
        )
    }
}

@Component
class ReviewerWorker(
    private val chatClient: ChatClient
) : Worker {

    override val type = WorkerType.REVIEWER

    override fun execute(
        task: SubTask,
        dependencyResults: Map<String, WorkerResult>
    ): WorkerResult {
        val toReview = dependencyResults.values
            .joinToString("\n---\n") { it.output }

        val output = chatClient.prompt()
            .system("""
                당신은 품질 검토 전문가입니다.
                제공된 작업물을 검토하고 피드백을 제공하세요.

                검토 항목:
                - 정확성
                - 완성도
                - 품질
                - 개선 제안

                심각한 문제가 있으면 requiresReplanning을 true로 설정하세요.
            """.trimIndent())
            .user("검토 대상:\n$toReview\n\n검토 요청: ${task.description}")
            .call()
            .content()

        val hasIssues = output.contains("심각한 문제") ||
                        output.contains("재작업 필요")

        return WorkerResult(
            taskId = task.id,
            output = output,
            success = true,
            requiresReplanning = hasIssues
        )
    }
}

// Writer, Analyst 등도 유사하게 구현...
```

### 4.4.4 의존성 관리 및 병렬 실행

의존성 그래프를 분석하여 가능한 많은 작업을 병렬로 실행합니다.

```kotlin
@Service
class DependencyAwareOrchestrator(
    private val workers: Map<WorkerType, Worker>
) {

    suspend fun execute(plan: TaskPlan): Map<String, WorkerResult> {
        val completedTasks = ConcurrentHashMap<String, WorkerResult>()

        while (completedTasks.size < plan.subTasks.size) {
            // 실행 가능한 태스크 찾기
            val readyTasks = plan.subTasks.filter { task ->
                !completedTasks.containsKey(task.id) &&
                task.dependencies.all { completedTasks.containsKey(it) }
            }.sortedBy { it.priority }

            if (readyTasks.isEmpty()) {
                if (completedTasks.size < plan.subTasks.size) {
                    throw IllegalStateException("Deadlock detected in task dependencies")
                }
                break
            }

            // 병렬 실행
            coroutineScope {
                readyTasks.map { task ->
                    async {
                        val dependencyResults = task.dependencies
                            .associateWith { completedTasks[it]!! }

                        val worker = workers[task.workerType]!!
                        val result = worker.execute(task, dependencyResults)

                        completedTasks[task.id] = result
                    }
                }.awaitAll()
            }
        }

        return completedTasks
    }

    // 의존성 그래프 시각화 (디버깅용)
    fun visualizeDependencies(plan: TaskPlan): String {
        val lines = mutableListOf<String>()
        lines.add("작업 의존성 그래프:")
        lines.add("=" .repeat(40))

        for (task in plan.subTasks) {
            val deps = if (task.dependencies.isEmpty()) {
                "없음 (즉시 실행 가능)"
            } else {
                task.dependencies.joinToString(", ")
            }
            lines.add("${task.id} (${task.workerType})")
            lines.add("  └─ 의존: $deps")
        }

        return lines.joinToString("\n")
    }
}
```

### 4.4.5 실습: 코드 생성 에이전트

요구사항을 받아 설계, 구현, 테스트, 리뷰까지 자동으로 수행하는 에이전트를 만들어 봅시다.

```kotlin
data class RequirementAnalysis(
    val summary: String,
    val functionalRequirements: List<String>,
    val nonFunctionalRequirements: List<String>,
    val constraints: List<String>
)

data class CodeGenerationResult(
    val code: IntegratedCode,
    val analysis: RequirementAnalysis,
    val validation: ValidationResult
)

data class IntegratedCode(
    val mainCode: String,
    val tests: String,
    val documentation: String
)

data class ValidationResult(
    val passed: Boolean,
    val issues: List<String>,
    val suggestions: List<String>
)

@Service
class CodeGenerationOrchestrator(
    private val chatClient: ChatClient,
    private val orchestrator: OrchestratorWorkflow
) {

    suspend fun generateCode(requirement: String): CodeGenerationResult {
        // 1. 요구사항 분석
        val analysis = analyzeRequirement(requirement)
        println("📋 요구사항 분석 완료")

        // 2. 태스크 계획 (자동 생성)
        val enhancedTask = """
            다음 요구사항에 맞는 코드를 생성하세요:

            요구사항 요약: ${analysis.summary}

            기능 요구사항:
            ${analysis.functionalRequirements.joinToString("\n") { "- $it" }}

            비기능 요구사항:
            ${analysis.nonFunctionalRequirements.joinToString("\n") { "- $it" }}

            제약사항:
            ${analysis.constraints.joinToString("\n") { "- $it" }}

            필요한 작업:
            1. 아키텍처 설계 (ANALYST)
            2. 코드 구현 (CODER) - 설계 의존
            3. 테스트 작성 (CODER) - 구현 의존
            4. 코드 리뷰 (REVIEWER) - 구현, 테스트 의존
        """.trimIndent()

        // 3. 오케스트레이터로 실행
        val result = orchestrator.execute(enhancedTask)
        println("✅ 코드 생성 완료 (${result.iterations} 반복)")

        // 4. 결과 통합
        val code = integrateCode(result.workerResults)

        // 5. 최종 검증
        var validation = validateCode(code)
        var finalCode = code

        if (!validation.passed) {
            println("⚠️ 검증 실패, 이슈 수정 중...")
            finalCode = fixIssues(code, validation.issues)
            validation = validateCode(finalCode)
        }

        return CodeGenerationResult(finalCode, analysis, validation)
    }

    private fun analyzeRequirement(requirement: String): RequirementAnalysis {
        return chatClient.prompt()
            .system("""
                요구사항을 분석하고 구조화하세요:
                - summary: 한 줄 요약
                - functionalRequirements: 기능 요구사항 목록
                - nonFunctionalRequirements: 비기능 요구사항 (성능, 보안 등)
                - constraints: 제약사항
            """.trimIndent())
            .user(requirement)
            .call()
            .entity(RequirementAnalysis::class.java)
    }

    private fun integrateCode(results: Map<String, WorkerResult>): IntegratedCode {
        // 결과에서 코드, 테스트, 문서 추출
        val coderResults = results.filterKeys { it.contains("coder") || it.contains("impl") }
        val testResults = results.filterKeys { it.contains("test") }
        val reviewResults = results.filterKeys { it.contains("review") }

        return IntegratedCode(
            mainCode = coderResults.values.firstOrNull()?.output ?: "",
            tests = testResults.values.firstOrNull()?.output ?: "",
            documentation = reviewResults.values
                .joinToString("\n") { it.output }
        )
    }

    private fun validateCode(code: IntegratedCode): ValidationResult {
        return chatClient.prompt()
            .system("""
                코드를 검증하세요:
                - 문법 오류
                - 논리적 문제
                - 보안 취약점
                - 베스트 프랙티스 준수

                passed: 심각한 이슈가 없으면 true
            """.trimIndent())
            .user("""
                코드:
                ```
                ${code.mainCode}
                ```

                테스트:
                ```
                ${code.tests}
                ```
            """.trimIndent())
            .call()
            .entity(ValidationResult::class.java)
    }

    private fun fixIssues(code: IntegratedCode, issues: List<String>): IntegratedCode {
        val fixedCode = chatClient.prompt()
            .system("""
                다음 이슈들을 수정한 코드를 제공하세요:
                ${issues.joinToString("\n") { "- $it" }}
            """.trimIndent())
            .user(code.mainCode)
            .call()
            .content()

        return code.copy(mainCode = fixedCode)
    }
}
```

---

## Module 4.5: Evaluator-Optimizer (평가자-최적화)

### 4.5.1 반복적 개선 패턴

**평가자-최적화** 패턴은 결과물을 평가하고, 기준에 미달하면 피드백을 반영하여 개선하는 과정을 반복합니다.

```
         ┌────────────────────────┐
         ↓                        │
[Input] → [Generator] → [Evaluator] → Pass? → [Output]
                              │
                              ↓ No
                          [Feedback]
```

### 4.5.2 구현

```kotlin
data class Evaluation(
    val score: Double,  // 0.0 ~ 1.0
    val completeness: Double,
    val accuracy: Double,
    val quality: Double,
    val relevance: Double,
    val feedback: String,
    val specificIssues: List<String>
)

data class Iteration(
    val number: Int,
    val output: String,
    val evaluation: Evaluation
)

data class OptimizationResult(
    val finalOutput: String,
    val iterations: List<Iteration>,
    val success: Boolean,
    val totalIterations: Int
) {
    companion object {
        fun success(output: String, iterations: List<Iteration>) =
            OptimizationResult(output, iterations, true, iterations.size)

        fun maxIterationsReached(output: String, iterations: List<Iteration>) =
            OptimizationResult(output, iterations, false, iterations.size)
    }
}

@Service
class EvaluatorOptimizerWorkflow(
    private val chatClient: ChatClient
) {
    companion object {
        private const val MAX_ITERATIONS = 5
        private const val PASS_THRESHOLD = 0.8
    }

    fun optimize(task: String): OptimizationResult {
        var currentOutput = generateInitial(task)
        val iterations = mutableListOf<Iteration>()

        for (i in 1..MAX_ITERATIONS) {
            // 평가
            val evaluation = evaluate(task, currentOutput)
            iterations.add(Iteration(i, currentOutput, evaluation))

            println("📊 반복 $i: 점수 ${String.format("%.2f", evaluation.score)}")

            // 통과 여부 확인
            if (evaluation.score >= PASS_THRESHOLD) {
                println("✅ 품질 기준 통과!")
                return OptimizationResult.success(currentOutput, iterations)
            }

            // 개선
            println("🔄 피드백 반영 중...")
            currentOutput = improve(task, currentOutput, evaluation.feedback)
        }

        println("⚠️ 최대 반복 횟수 도달")
        return OptimizationResult.maxIterationsReached(currentOutput, iterations)
    }

    private fun generateInitial(task: String): String {
        return chatClient.prompt()
            .system("주어진 작업에 대한 초기 결과물을 생성하세요.")
            .user(task)
            .call()
            .content()
    }

    private fun evaluate(task: String, output: String): Evaluation {
        return chatClient.prompt()
            .system("""
                결과물을 원래 작업 요구사항과 비교하여 평가하세요.

                각 항목을 0.0 ~ 1.0으로 평가:
                - completeness: 작업을 완전히 수행했는가?
                - accuracy: 정보가 정확한가?
                - quality: 품질이 좋은가 (문체, 구조 등)?
                - relevance: 주제에서 벗어나지 않았는가?

                score는 위 항목의 가중 평균 (completeness 30%, accuracy 30%, quality 20%, relevance 20%)

                구체적이고 실행 가능한 피드백을 제공하세요.
            """.trimIndent())
            .user("""
                작업: $task

                평가할 결과물:
                $output
            """.trimIndent())
            .call()
            .entity(Evaluation::class.java)
    }

    private fun improve(
        task: String,
        currentOutput: String,
        feedback: String
    ): String {
        return chatClient.prompt()
            .system("""
                피드백을 반영하여 결과물을 개선하세요.
                잘 된 부분은 유지하고, 피드백의 각 포인트를 해결하세요.
            """.trimIndent())
            .user("""
                원래 작업: $task

                현재 결과물:
                $currentOutput

                개선할 피드백:
                $feedback

                개선된 버전:
            """.trimIndent())
            .call()
            .content()
    }
}
```

### 4.5.3 실습: 코드 리뷰 및 개선 에이전트

코드를 리뷰하고 자동으로 개선하는 에이전트를 만들어 봅시다.

```kotlin
data class CodeIssue(
    val severity: Severity,
    val location: String,
    val description: String,
    val suggestion: String
)

enum class Severity { CRITICAL, HIGH, MEDIUM, LOW }

data class CodeReview(
    val issues: List<CodeIssue>,
    val overallQuality: Double,
    val strengths: List<String>,
    val suggestions: List<String>
)

data class ReviewCycle(
    val cycleNumber: Int,
    val code: String,
    val review: CodeReview
)

data class CodeOptimizationResult(
    val finalCode: String,
    val cycles: List<ReviewCycle>,
    val totalIssuesFixed: Int
)

@Service
class CodeReviewOptimizer(
    private val chatClient: ChatClient
) {

    fun optimizeCode(
        code: String,
        requirements: String
    ): CodeOptimizationResult {
        var currentCode = code
        val cycles = mutableListOf<ReviewCycle>()
        var totalFixed = 0

        repeat(3) { i ->
            // 코드 리뷰
            val review = reviewCode(currentCode, requirements)
            cycles.add(ReviewCycle(i + 1, currentCode, review))

            println("📝 리뷰 사이클 ${i + 1}: ${review.issues.size}개 이슈 발견")

            // 모든 이슈 해결됨
            if (review.issues.isEmpty()) {
                println("✅ 코드 품질 검증 완료!")
                return CodeOptimizationResult(currentCode, cycles, totalFixed)
            }

            // 이슈별로 정렬 (심각도 높은 순)
            val sortedIssues = review.issues.sortedBy {
                when (it.severity) {
                    Severity.CRITICAL -> 0
                    Severity.HIGH -> 1
                    Severity.MEDIUM -> 2
                    Severity.LOW -> 3
                }
            }

            println("  - CRITICAL: ${sortedIssues.count { it.severity == Severity.CRITICAL }}")
            println("  - HIGH: ${sortedIssues.count { it.severity == Severity.HIGH }}")
            println("  - MEDIUM: ${sortedIssues.count { it.severity == Severity.MEDIUM }}")
            println("  - LOW: ${sortedIssues.count { it.severity == Severity.LOW }}")

            // 코드 개선
            currentCode = improveCode(currentCode, review)
            totalFixed += review.issues.size
        }

        return CodeOptimizationResult(currentCode, cycles, totalFixed)
    }

    private fun reviewCode(code: String, requirements: String): CodeReview {
        return chatClient.prompt()
            .system("""
                코드를 다음 관점에서 리뷰하세요:

                1. 정확성 - 요구사항을 충족하는가?
                2. 성능 - 비효율적인 부분이 있는가?
                3. 보안 - 취약점이 있는가?
                4. 유지보수성 - 깔끔하고 읽기 쉬운가?
                5. 베스트 프랙티스 - 컨벤션을 따르는가?

                각 이슈에 대해:
                - severity: CRITICAL, HIGH, MEDIUM, LOW
                - location: 파일/줄 번호 또는 섹션
                - description: 무엇이 문제인가
                - suggestion: 어떻게 수정하면 좋은가

                strengths에 잘 된 부분도 언급하세요.
            """.trimIndent())
            .user("""
                요구사항:
                $requirements

                코드:
                ```
                $code
                ```
            """.trimIndent())
            .call()
            .entity(CodeReview::class.java)
    }

    private fun improveCode(code: String, review: CodeReview): String {
        val issuesSummary = review.issues.joinToString("\n") { issue ->
            "[${issue.severity}] ${issue.location}: ${issue.description}\n  → ${issue.suggestion}"
        }

        return chatClient.prompt()
            .system("""
                리뷰 결과를 반영하여 코드를 수정하세요.
                각 이슈를 해결하되, 코드의 장점은 유지하세요.

                장점 (유지할 것):
                ${review.strengths.joinToString("\n") { "- $it" }}
            """.trimIndent())
            .user("""
                원본 코드:
                ```
                $code
                ```

                수정할 이슈들:
                $issuesSummary

                수정된 코드:
            """.trimIndent())
            .call()
            .content()
    }
}
```

---

## Module 4.6: Reflection Agent (반성 에이전트)

### 4.6.1 자기 반성 패턴

**반성 에이전트**는 자신의 응답을 스스로 비판적으로 검토하고 개선합니다. 마치 글을 쓰고 나서 다시 읽어보며 고치는 것과 같습니다.

### 4.6.2 구현

```kotlin
data class Reflection(
    val strengths: List<String>,
    val weaknesses: List<String>,
    val assumptions: List<String>,
    val improvementAreas: List<String>,
    val needsImprovement: Boolean,
    val selfConfidence: Double  // 0.0 ~ 1.0
)

data class Verification(
    val factuallyCorrect: Boolean,
    val logicallySound: Boolean,
    val complete: Boolean,
    val overallAssessment: String
)

data class ReflectionResult(
    val finalResponse: String,
    val initialResponse: String,
    val reflection: Reflection,
    val verification: Verification,
    val wasImproved: Boolean
)

@Service
class ReflectionAgent(
    private val chatClient: ChatClient
) {

    fun generateWithReflection(task: String): ReflectionResult {
        // 1. 초기 응답 생성
        val initialResponse = generate(task)
        println("📝 초기 응답 생성 완료")

        // 2. 자기 반성
        val reflection = reflect(task, initialResponse)
        println("🤔 자기 반성 완료")
        println("  - 강점: ${reflection.strengths.size}개")
        println("  - 약점: ${reflection.weaknesses.size}개")
        println("  - 자신감: ${String.format("%.0f", reflection.selfConfidence * 100)}%")

        // 3. 반성 기반 개선
        val improvedResponse = if (reflection.needsImprovement) {
            println("🔄 응답 개선 중...")
            improveBasedOnReflection(task, initialResponse, reflection)
        } else {
            println("✅ 개선 불필요")
            initialResponse
        }

        // 4. 최종 검증
        val verification = verify(task, improvedResponse)
        println("✔️ 검증 완료: ${verification.overallAssessment}")

        return ReflectionResult(
            finalResponse = improvedResponse,
            initialResponse = initialResponse,
            reflection = reflection,
            verification = verification,
            wasImproved = reflection.needsImprovement
        )
    }

    private fun generate(task: String): String {
        return chatClient.prompt()
            .system("주어진 작업에 대해 최선의 응답을 생성하세요.")
            .user(task)
            .call()
            .content()
    }

    private fun reflect(task: String, response: String): Reflection {
        return chatClient.prompt()
            .system("""
                자신의 응답을 비판적으로 분석하세요.

                다음을 고려하세요:
                1. 작업을 완전히 이해했는가?
                2. 모든 요구사항을 다뤘는가?
                3. 논리적 오류나 빈틈이 있는가?
                4. 응답이 오해될 소지가 있는가?
                5. 어떤 가정을 했는가?
                6. 무엇을 더 잘 할 수 있었는가?

                솔직하고 철저하게 자기 평가를 하세요.
                needsImprovement는 개선이 필요하면 true, 충분히 좋으면 false.
            """.trimIndent())
            .user("""
                작업: $task

                내 응답:
                $response

                자기 반성:
            """.trimIndent())
            .call()
            .entity(Reflection::class.java)
    }

    private fun improveBasedOnReflection(
        task: String,
        originalResponse: String,
        reflection: Reflection
    ): String {
        return chatClient.prompt()
            .system("""
                자기 반성 결과를 바탕으로 응답을 개선하세요.

                강점 (유지할 것):
                ${reflection.strengths.joinToString("\n") { "- $it" }}

                약점 (개선할 것):
                ${reflection.weaknesses.joinToString("\n") { "- $it" }}

                개선 영역:
                ${reflection.improvementAreas.joinToString("\n") { "- $it" }}
            """.trimIndent())
            .user("""
                원래 작업: $task

                원래 응답:
                $originalResponse

                개선된 응답:
            """.trimIndent())
            .call()
            .content()
    }

    private fun verify(task: String, response: String): Verification {
        return chatClient.prompt()
            .system("""
                응답을 최종 검증하세요:

                - factuallyCorrect: 사실적으로 정확한가?
                - logicallySound: 논리적으로 타당한가?
                - complete: 완전한가 (빠진 것이 없는가)?
                - overallAssessment: 종합 평가 (한 문장)
            """.trimIndent())
            .user("""
                작업: $task

                응답:
                $response
            """.trimIndent())
            .call()
            .entity(Verification::class.java)
    }
}
```

### 4.6.3 다중 반성 (Multi-turn Reflection)

더 높은 품질을 위해 여러 번 반성을 반복할 수도 있습니다.

```kotlin
@Service
class MultiTurnReflectionAgent(
    private val chatClient: ChatClient
) {
    companion object {
        private const val MAX_REFLECTION_TURNS = 3
        private const val CONFIDENCE_THRESHOLD = 0.85
    }

    fun generateWithMultipleReflections(task: String): ReflectionResult {
        var currentResponse = generate(task)
        var bestReflection: Reflection? = null

        for (turn in 1..MAX_REFLECTION_TURNS) {
            println("🔄 반성 턴 $turn")

            val reflection = reflect(task, currentResponse)
            bestReflection = reflection

            // 충분히 좋으면 종료
            if (reflection.selfConfidence >= CONFIDENCE_THRESHOLD &&
                !reflection.needsImprovement) {
                println("✅ 충분한 품질 달성 (자신감: ${reflection.selfConfidence})")
                break
            }

            // 개선
            currentResponse = improveBasedOnReflection(task, currentResponse, reflection)
        }

        val verification = verify(task, currentResponse)

        return ReflectionResult(
            finalResponse = currentResponse,
            initialResponse = currentResponse,  // 첫 응답 저장 필요 시 수정
            reflection = bestReflection!!,
            verification = verification,
            wasImproved = true
        )
    }

    // generate, reflect, improve, verify 메서드는 위와 동일...
}
```

---

## Part 4 요약

### 이 파트에서 배운 것

#### Agentic AI: 지시 실행에서 자율 행동으로

전통적인 AI 애플리케이션이 "질문-응답" 패러다임에 머물렀다면, Agentic Pattern은 AI가 **목표를 이해하고 스스로 계획을 수립하여 실행**하는 패러다임으로의 전환을 의미합니다. 이는 단순히 더 많은 함수를 호출하는 것이 아니라, 작업을 분해하고, 적절한 도구를 선택하고, 결과를 평가하여 다음 행동을 결정하는 **자율적 의사결정 능력**을 부여하는 것입니다.

#### 패턴은 재사용 가능한 설계 지식

6가지 핵심 패턴(Chain, Parallelization, Routing, Orchestrator-Workers, Evaluator-Optimizer, Reflection)은 AI 시스템 설계에서 반복적으로 등장하는 문제에 대한 **검증된 해결책**입니다. 각 패턴은 특정 상황에서의 트레이드오프를 명확히 하며, 실무에서는 이들을 조합하여 복잡한 요구사항을 충족시킵니다. 패턴을 이해하면 문제를 보는 관점이 달라지고, 설계 결정의 근거가 명확해집니다.

#### 복잡성 관리와 신뢰성 확보

Agentic 시스템은 강력하지만, 제어되지 않으면 예측 불가능해질 수 있습니다. Evaluator-Optimizer 패턴은 출력 품질을 보장하고, Reflection 패턴은 AI가 스스로 오류를 발견하고 수정하도록 합니다. 이러한 **자기 검증 메커니즘**은 프로덕션 환경에서 AI 시스템의 신뢰성을 확보하는 핵심 요소입니다. 비용과 정확도, 속도와 품질 사이의 균형점을 찾는 것이 Agentic 시스템 설계의 핵심 과제입니다.

### 패턴 비교표

| 패턴 | 사용 시점 | 특징 | 장점 | 단점 |
|------|----------|------|------|------|
| **Chain** | 순차적 단계 필요 | 단계별 처리 | 단순, 예측 가능 | 느릴 수 있음 |
| **Parallelization** | 독립적 작업 | 동시 실행 | 빠름 | 복잡한 집계 |
| **Routing** | 유형별 처리 | 분류 후 전달 | 전문화 | 분류 정확도 의존 |
| **Orchestrator** | 복잡한 동적 작업 | 동적 분해/할당 | 유연, 적응적 | 오버헤드 |
| **Evaluator** | 품질 중요 | 반복 개선 | 품질 보장 | 시간 소요 |
| **Reflection** | 정확도 중요 | 자기 검증 | 신뢰성 | 비용 |

### 패턴 선택 가이드

```
질문: 작업이 어떤 특성을 가지고 있나요?

├── 순서가 중요하다 → Chain Workflow
│
├── 독립적인 작업들이다 → Parallelization
│
├── 입력 유형에 따라 처리가 다르다 → Routing
│
├── 복잡하고 동적이다 → Orchestrator-Workers
│
├── 품질이 중요하다 → Evaluator-Optimizer
│
└── 정확도가 매우 중요하다 → Reflection Agent
```

### 패턴 조합

실제 시스템에서는 여러 패턴을 조합해서 사용합니다:

```kotlin
// 예: Routing + Chain + Evaluator 조합
class HybridWorkflow {
    fun process(input: String): String {
        // 1. 라우팅으로 작업 유형 결정
        val type = router.classify(input)

        // 2. 체인으로 단계별 처리
        val result = when (type) {
            Type.SIMPLE -> simpleChain.process(input)
            Type.COMPLEX -> complexChain.process(input)
        }

        // 3. 평가자로 품질 검증 및 개선
        return evaluator.optimize(result)
    }
}
```

### 실전 활용 팁

#### 패턴 선택 기준
- **단순함 우선**: 복잡한 패턴이 항상 좋은 것은 아닙니다. Chain으로 충분하면 Orchestrator를 쓰지 마세요
- **점진적 복잡화**: 단순한 패턴으로 시작하고, 필요에 따라 복잡한 패턴으로 발전시키세요
- **측정 기반 결정**: 성능, 비용, 품질 메트릭을 수집하여 패턴 선택의 근거로 삼으세요

#### 프로덕션 고려사항
- **타임아웃 설정**: 각 단계별 타임아웃과 전체 워크플로우 타임아웃을 별도로 관리하세요
- **부분 실패 처리**: Parallelization에서 일부 작업이 실패해도 전체가 실패하지 않도록 설계하세요
- **비용 제어**: Evaluator나 Reflection의 반복 횟수에 상한을 두어 비용 폭주를 방지하세요

#### 디버깅과 모니터링
- **중간 상태 로깅**: 각 단계의 입력/출력을 기록하여 문제 발생 시 추적 가능하게 하세요
- **메트릭 수집**: 단계별 소요 시간, 토큰 사용량, 성공/실패율을 모니터링하세요
- **재현 가능성**: 동일 입력에 대해 동일 결과를 얻을 수 있도록 시드 값을 관리하세요

### 자주 하는 실수

| 실수 | 문제점 | 해결 방법 |
|------|--------|----------|
| 과도한 패턴 복잡성 | 유지보수 어려움, 디버깅 난이도 증가 | 단순한 패턴으로 시작, 필요시 확장 |
| 무한 루프 미방지 | Evaluator/Reflection의 종료 조건 없음 | 최대 반복 횟수 설정, 개선율 임계값 적용 |
| 에러 전파 미처리 | 중간 단계 실패 시 전체 시스템 중단 | 폴백 전략, 부분 결과 반환, 재시도 로직 |
| 컨텍스트 손실 | 단계 간 필요한 정보가 전달되지 않음 | 명시적 컨텍스트 객체 설계, 상태 관리 |
| 비용 통제 실패 | 예상치 못한 API 비용 폭주 | 단계별/전체 토큰 한도, 비용 알림 설정 |

### 학습 체크리스트

- [ ] Chain Workflow로 순차적 파이프라인 구현
- [ ] Parallelization으로 동시 처리 구현
- [ ] Routing으로 입력 분류 및 분기 처리
- [ ] Orchestrator-Workers로 동적 작업 분배
- [ ] Evaluator-Optimizer로 품질 개선 루프 구현
- [ ] Reflection Agent로 자기 검증 시스템 구현
- [ ] 여러 패턴의 조합 설계 및 구현

---

## 다음 단계

Part 4에서 자율적인 AI 에이전트 패턴을 익혔다면, 이제 이 도구들을 **표준화된 방식으로 공유하고 재사용**하는 방법을 배울 차례입니다.

**Part 5: Model Context Protocol (MCP)**에서 배울 내용:

| 주제 | 설명 | 활용 예시 |
|------|------|----------|
| **MCP 아키텍처** | 표준화된 AI 도구 통합 프로토콜 이해 | 다양한 AI 클라이언트 지원 |
| **MCP Server 구축** | WebMVC, WebFlux, STDIO 기반 서버 구현 | 사내 도구 MCP화, 레거시 시스템 연동 |
| **MCP Client** | 외부 MCP 서버와의 연동 | Claude Desktop, VS Code 등과 통합 |
| **Dynamic Tool Update** | 런타임 도구 추가/제거 | 플러그인 시스템, 동적 기능 확장 |
| **Sampling** | MCP를 통한 AI 호출 | 서버 측 AI 응답 생성 |

MCP는 AI 도구 생태계의 **USB 포트**와 같습니다 - 표준화된 인터페이스로 어떤 도구든 연결할 수 있습니다!

---

## 연습 문제

1. **Chain Workflow**: 블로그 포스트 생성 파이프라인을 만들어 보세요.
   - 주제 → 아웃라인 → 본문 → SEO 최적화 → 최종본

2. **Parallelization**: 뉴스 기사를 여러 언어로 동시에 번역하는 시스템을 만들어 보세요.

3. **Routing**: FAQ 봇을 만들어 보세요.
   - 기술/결제/배송/일반 문의를 분류하고 적절히 응답

4. **Orchestrator**: 간단한 프로젝트 관리 에이전트를 만들어 보세요.
   - 요구사항을 받아 태스크 분해 및 할당

5. **Evaluator**: 에세이 작성 및 자동 평가/개선 시스템을 만들어 보세요.

6. **Reflection**: 면접 질문 답변 연습 에이전트를 만들어 보세요.
   - 답변 후 자기 평가 및 개선 제안

---

## 참고 예제 코드

이 책의 예제 코드는 다음 디렉토리에서 찾을 수 있습니다:

```
spring-ai-examples/
├── agentic-patterns/
│   ├── chain-workflow/          # Chain 패턴
│   ├── parallelization-workflow/ # 병렬화 패턴
│   ├── routing-workflow/        # 라우팅 패턴
│   ├── orchestrator-workers/    # 오케스트레이터 패턴
│   └── evaluator-optimizer/     # 평가-최적화 패턴
└── agents/
    └── reflection/              # Reflection 에이전트
```
