"""
数字朋友服务
处理数字朋友的创建、素材管理、人格蒸馏（LLM生成系统提示词）
"""

import json
import re
import asyncio
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.core.logging import get_logger
from app.models.db.digital_friend import DigitalFriend
from app.ai.llm.dashscope_client import dashscope_client

logger = get_logger(__name__)

# status 状态值
STATUS_DRAFT = "draft"
STATUS_PROCESSING = "processing"
STATUS_CALIBRATING = "calibrating"
STATUS_READY = "ready"
STATUS_FAILED = "failed"


async def create_friend(
    db: AsyncSession,
    user_id: int,
    name: str,
    description: str | None = None,
    avatar_url: str | None = None,
) -> dict:
    """
    创建数字朋友

    Args:
        db: 数据库会话
        user_id: 用户ID
        name: 朋友昵称
        description: 一句话描述
        avatar_url: 头像URL
    """
    friend = DigitalFriend(
        user_id=user_id,
        name=name,
        description=description,
        avatar_url=avatar_url,
        status=STATUS_DRAFT,
    )
    db.add(friend)
    await db.flush()
    await db.refresh(friend)

    logger.info(f"数字朋友已创建: id={friend.id}, name={name}, user={user_id}")
    return _to_response(friend)


async def get_friend(
    db: AsyncSession,
    user_id: int,
    friend_id: int,
) -> dict:
    """获取数字朋友详情"""
    friend = await _get_owned_friend(db, user_id, friend_id)
    return _to_response(friend)


async def list_friends(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """获取数字朋友列表（分页）"""
    # 总数
    count_stmt = (
        select(func.count())
        .select_from(DigitalFriend)
        .where(
            DigitalFriend.user_id == user_id,
            DigitalFriend.is_deleted == False,
        )
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    # 分页查询
    stmt = (
        select(DigitalFriend)
        .where(
            DigitalFriend.user_id == user_id,
            DigitalFriend.is_deleted == False,
        )
        .order_by(DigitalFriend.create_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    friends = result.scalars().all()

    return {
        "list": [_to_response(f) for f in friends],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


async def update_friend(
    db: AsyncSession,
    user_id: int,
    friend_id: int,
    name: str | None = None,
    description: str | None = None,
    avatar_url: str | None = None,
) -> dict:
    """更新数字朋友信息"""
    friend = await _get_owned_friend(db, user_id, friend_id)

    if name is not None:
        friend.name = name
    if description is not None:
        friend.description = description
    if avatar_url is not None:
        friend.avatar_url = avatar_url

    friend.update_time = datetime.now()
    await db.flush()

    logger.info(f"数字朋友已更新: id={friend_id}")
    return _to_response(friend)


async def delete_friend(
    db: AsyncSession,
    user_id: int,
    friend_id: int,
) -> dict:
    """删除数字朋友（软删除）"""
    friend = await _get_owned_friend(db, user_id, friend_id)

    friend.is_deleted = True
    friend.update_time = datetime.now()
    await db.flush()

    logger.info(f"数字朋友已删除: id={friend_id}")
    return {"success": True}


async def save_source_materials(
    db: AsyncSession,
    user_id: int,
    friend_id: int,
    materials: list[dict],
) -> dict:
    """
    保存素材到数字朋友

    Args:
        materials: 素材列表，每项包含 type 和 content
            例: [{"type": "chat_log", "content": "..."}, {"type": "hobby", "content": "..."}]
    """
    friend = await _get_owned_friend(db, user_id, friend_id)

    # 合并到现有素材
    existing = []
    if friend.source_materials:
        try:
            existing = json.loads(friend.source_materials)
        except (json.JSONDecodeError, TypeError):
            existing = []

    existing.extend(materials)
    friend.source_materials = json.dumps(existing, ensure_ascii=False)
    friend.update_time = datetime.now()

    # 如果之前已经蒸馏过，素材更新后重置状态为 draft
    if friend.status in (STATUS_READY, STATUS_CALIBRATING):
        friend.status = STATUS_DRAFT
        friend.system_prompt = None
        friend.calibration_questions = None
        friend.calibration_answers = None

    await db.flush()

    logger.info(f"素材已保存: friend={friend_id}, 新增{len(materials)}条, 共{len(existing)}条")
    return {
        "friend_id": friend_id,
        "total_materials": len(existing),
    }


async def generate_system_prompt(
    db: AsyncSession,
    user_id: int,
    friend_id: int,
) -> dict:
    """
    触发人格蒸馏：分析素材 → 生成校准问题 → 进入校准阶段

    流程：
    1. 读取所有素材，做摘要压缩
    2. 基于摘要分析素材，生成 3~5 个针对性校准问题
    3. 状态变为 calibrating，等待用户回答
    """
    friend = await _get_owned_friend(db, user_id, friend_id)

    if not friend.source_materials:
        raise BusinessException(400, "请先上传素材")

    # 检查是否已在处理中或已完成
    if friend.status == STATUS_PROCESSING:
        raise BusinessException(400, "正在处理中，请稍后")
    if friend.status == STATUS_CALIBRATING:
        raise BusinessException(400, "已进入校准阶段，请先完成校准")
    if friend.status == STATUS_READY:
        raise BusinessException(400, "人格已生成，如需重新生成请先删除该朋友再重建")

    # 更新状态为处理中
    friend.status = STATUS_PROCESSING
    friend.update_time = datetime.now()
    await db.flush()

    # 异步执行：摘要素材 + 生成校准问题
    asyncio.create_task(_generate_calibration_questions(friend.id, friend.name, friend.description or ""))

    logger.info(f"人格蒸馏已触发（校准模式）: friend={friend_id}")
    return {
        "friend_id": friend_id,
        "status": STATUS_PROCESSING,
        "message": "正在分析素材，即将进入校准阶段",
    }


async def get_friend_status(
    db: AsyncSession,
    user_id: int,
    friend_id: int,
) -> dict:
    """获取数字朋友状态"""
    friend = await _get_owned_friend(db, user_id, friend_id)
    result = {
        "friend_id": friend.id,
        "status": friend.status,
        "has_prompt": bool(friend.system_prompt),
    }
    # 如果在校准阶段，返回校准问题
    if friend.status == STATUS_CALIBRATING and friend.calibration_questions:
        result["calibration_questions"] = json.loads(friend.calibration_questions)
    return result


async def get_calibration_questions(
    db: AsyncSession,
    user_id: int,
    friend_id: int,
) -> dict:
    """获取校准问题"""
    friend = await _get_owned_friend(db, user_id, friend_id)

    if friend.status != STATUS_CALIBRATING:
        raise BusinessException(400, "当前不在校准阶段")

    questions = []
    if friend.calibration_questions:
        questions = json.loads(friend.calibration_questions)

    answers = []
    if friend.calibration_answers:
        answers = json.loads(friend.calibration_answers)

    return {
        "friend_id": friend_id,
        "status": friend.status,
        "questions": questions,
        "answers": answers,
    }


async def save_calibration_answers(
    db: AsyncSession,
    user_id: int,
    friend_id: int,
    answers: list[dict],
) -> dict:
    """
    保存校准回答

    Args:
        answers: 回答列表，格式 [{"question": "...", "answer": "..."}, ...]
    """
    friend = await _get_owned_friend(db, user_id, friend_id)

    if friend.status != STATUS_CALIBRATING:
        raise BusinessException(400, "当前不在校准阶段")

    friend.calibration_answers = json.dumps(answers, ensure_ascii=False)
    friend.update_time = datetime.now()
    await db.flush()

    logger.info(f"校准回答已保存: friend={friend_id}, {len(answers)}条回答")
    return {
        "friend_id": friend_id,
        "status": STATUS_CALIBRATING,
        "message": "回答已保存，点击完成校准生成最终人格",
    }


async def finalize_calibration(
    db: AsyncSession,
    user_id: int,
    friend_id: int,
) -> dict:
    """
    完成校准：结合素材摘要 + 校准回答，生成最终的 system_prompt
    """
    friend = await _get_owned_friend(db, user_id, friend_id)

    if friend.status != STATUS_CALIBRATING:
        raise BusinessException(400, "当前不在校准阶段")

    if not friend.calibration_answers:
        raise BusinessException(400, "请先回答校准问题")

    # 更新状态为处理中
    friend.status = STATUS_PROCESSING
    friend.update_time = datetime.now()
    await db.flush()

    # 异步执行最终蒸馏
    asyncio.create_task(_finalize_distill_async(friend.id, friend.name, friend.description or ""))

    logger.info(f"校准完成，开始最终蒸馏: friend={friend_id}")
    return {
        "friend_id": friend_id,
        "status": STATUS_PROCESSING,
        "message": "正在生成最终人格，稍后可查看结果",
    }


# ===== 内部方法 =====


async def _get_owned_friend(
    db: AsyncSession,
    user_id: int,
    friend_id: int,
) -> DigitalFriend:
    """获取并校验数字朋友归属"""
    stmt = select(DigitalFriend).where(
        DigitalFriend.id == friend_id,
        DigitalFriend.user_id == user_id,
        DigitalFriend.is_deleted == False,
    )
    result = await db.execute(stmt)
    friend = result.scalar_one_or_none()

    if not friend:
        raise BusinessException(400, "数字朋友不存在或无权访问")

    return friend


async def _distill_async(friend_id: int, name: str, description: str):
    """
    异步人格蒸馏任务

    在后台异步执行，不阻塞API请求。
    完成后更新 digital_friend 的 system_prompt 和 status。
    """
    from app.core.database import async_session

    db = None
    try:
        db = async_session()

        # 1. 读取数字朋友
        stmt = select(DigitalFriend).where(DigitalFriend.id == friend_id)
        result = await db.execute(stmt)
        friend = result.scalar_one_or_none()

        if not friend or not friend.source_materials:
            await _update_status(db, friend_id, STATUS_FAILED)
            return

        # 2. 解析素材
        materials = json.loads(friend.source_materials)

        # 3. 构建蒸馏提示词
        distilled_prompt = _build_distill_prompt(name, description, materials)

        # 4. 如果素材总字数超过8000，先做摘要压缩
        total_chars = sum(len(m.get("content", "")) for m in materials)
        if total_chars > 8000:
            logger.info(f"素材过长({total_chars}字)，先做摘要压缩: friend={friend_id}")
            summary = await _summarize_materials(materials)
            distilled_prompt = _build_distill_prompt_from_summary(name, description, summary)

        # 5. 调用LLM生成系统提示词
        logger.info(f"正在调用LLM生成系统提示词: friend={friend_id}, name={name}")
        system_prompt = dashscope_client.chat(
            messages=[{"role": "user", "content": distilled_prompt}],
            stream=False,
        )

        # 6. 更新数据库
        friend.system_prompt = system_prompt.strip()
        friend.status = STATUS_READY
        friend.update_time = datetime.now()
        await db.commit()

        logger.info(f"人格蒸馏完成: friend={friend_id}, name={name}")

    except Exception as e:
        logger.error(f"人格蒸馏失败: friend={friend_id}, error={e}")
        try:
            if db:
                await _update_status(db, friend_id, STATUS_FAILED)
        except Exception:
            pass
    finally:
        if db:
            await db.close()


async def _generate_calibration_questions(friend_id: int, name: str, description: str):
    """
    异步任务：分析素材 → 生成校准问题

    1. 读取素材并做摘要
    2. 基于摘要让 LLM 分析哪些人格维度信息不足
    3. 生成 3~5 个针对性校准问题
    4. 状态变为 calibrating
    """
    from app.core.database import async_session

    db = None
    try:
        db = async_session()

        # 1. 读取数字朋友
        stmt = select(DigitalFriend).where(DigitalFriend.id == friend_id)
        result = await db.execute(stmt)
        friend = result.scalar_one_or_none()

        if not friend or not friend.source_materials:
            await _update_status(db, friend_id, STATUS_FAILED)
            return

        # 2. 解析素材
        materials = json.loads(friend.source_materials)

        # 3. 摘要素材（复用已有逻辑）
        total_chars = sum(len(m.get("content", "")) for m in materials)
        if total_chars > 8000:
            summary = await _summarize_materials(materials)
        else:
            summary = _build_materials_text(materials)

        # 4. 让 LLM 分析信息缺口，生成校准问题
        logger.info(f"正在生成校准问题: friend={friend_id}, name={name}")
        questions_prompt = f"""你是一位专业的人格分析师。你正在帮助用户创建一个名为"{name}"的数字朋友。

以下是关于{name}的已知信息：

{description if description else "（用户未提供描述）"}

{summary}

请分析以上信息，找出哪些关键人格维度的信息不够充分，需要向用户进一步确认。
生成 3~5 个针对性的校准问题，帮助补全{name}的人格画像。

## 问题设计原则
1. 每个问题针对一个具体的人格维度（说话风格/性格/价值观/情感表达/社交方式等）
2. 问题要具体，不要笼统（"他遇到压力时一般怎么排解？" 比 "说说他的性格" 好）
3. 提供选项参考，降低用户回答门槛
4. 如果素材中已有充分信息的维度，不要重复提问

## 输出格式
返回纯 JSON 数组，每个元素包含 id 和 question 字段：
[
    {{"id": 1, "question": "问题内容", "options": ["选项A", "选项B", "选项C"]}},
    ...
]

只输出 JSON，不要有其他文字。"""

        response = dashscope_client.chat(
            messages=[{"role": "user", "content": questions_prompt}],
            stream=False,
        )

        # 5. 解析问题列表
        questions = _parse_json_array(response)
        if not questions:
            # fallback: 生成默认问题
            questions = _default_calibration_questions(name)

        logger.info(f"校准问题已生成: friend={friend_id}, {len(questions)}个问题")

        # 6. 更新数据库
        friend.calibration_questions = json.dumps(questions, ensure_ascii=False)
        friend.status = STATUS_CALIBRATING
        friend.update_time = datetime.now()
        await db.commit()

    except Exception as e:
        logger.error(f"生成校准问题失败: friend={friend_id}, error={e}")
        try:
            if db:
                await _update_status(db, friend_id, STATUS_FAILED)
        except Exception:
            pass
    finally:
        if db:
            await db.close()


async def _finalize_distill_async(friend_id: int, name: str, description: str):
    """
    异步任务：结合素材摘要 + 校准回答 → 生成最终 system_prompt
    """
    from app.core.database import async_session

    db = None
    try:
        db = async_session()

        # 1. 读取数字朋友
        stmt = select(DigitalFriend).where(DigitalFriend.id == friend_id)
        result = await db.execute(stmt)
        friend = result.scalar_one_or_none()

        if not friend or not friend.source_materials:
            await _update_status(db, friend_id, STATUS_FAILED)
            return

        # 2. 解析素材并摘要
        materials = json.loads(friend.source_materials)
        total_chars = sum(len(m.get("content", "")) for m in materials)
        if total_chars > 8000:
            material_summary = await _summarize_materials(materials)
        else:
            material_summary = _build_materials_text(materials)

        # 3. 解析校准回答
        calibration_text = ""
        if friend.calibration_answers:
            answers = json.loads(friend.calibration_answers)
            calibration_text = "\n".join([
                f"Q: {a.get('question', '')}\nA: {a.get('answer', '')}"
                for a in answers
            ])

        # 4. 构建最终蒸馏 prompt
        final_prompt = f"""你是一位专业的人格分析师。请根据以下关于"{name}"的所有信息，生成一段完整的系统提示词。

这段系统提示词将用于让AI扮演{name}，模拟他的说话风格和性格来与用户对话。

## 关于{name}的描述
{description if description else "（用户未提供描述）"}

## {name}的素材摘要
{material_summary}

## 用户校准补充信息
{calibration_text if calibration_text else "（用户未提供额外信息）"}

## 要求
请生成一段系统提示词，包含以下维度：
1. **身份设定**：你是{name}，一个真实存在的人
2. **说话风格**：语气、口头禅、常用表情、句式特点、正式程度
3. **性格特点**：主要性格特征、处事方式
4. **兴趣爱好**：喜欢的事物、话题
5. **价值观**：核心信念、人生态度
6. **情感表达**：情绪表达方式、支持他人的方式
7. **社交方式**：与朋友相处的模式

**重要**：校准回答中的信息优先级高于素材摘要。如果校准回答和素材有冲突，以校准回答为准。

## 输出格式
直接输出系统提示词的正文，不要加代码块标记。系统提示词应该能让AI完全模拟{name}的人格来对话。

注意：
- 始终以{name}的第一人称视角
- 要具体、生动，不要泛泛而谈
- 如果素材中有具体的口头禅、表情习惯，一定要体现出来
- 末尾加上对话规则：保持人格一致性、不暴露是AI"""

        # 5. 调用 LLM 生成最终系统提示词
        logger.info(f"正在生成最终系统提示词: friend={friend_id}, name={name}")
        system_prompt = dashscope_client.chat(
            messages=[{"role": "user", "content": final_prompt}],
            stream=False,
        )

        # 6. 更新数据库
        friend.system_prompt = system_prompt.strip()
        friend.status = STATUS_READY
        friend.update_time = datetime.now()
        await db.commit()

        logger.info(f"最终蒸馏完成: friend={friend_id}, name={name}")

    except Exception as e:
        logger.error(f"最终蒸馏失败: friend={friend_id}, error={e}")
        try:
            if db:
                await _update_status(db, friend_id, STATUS_FAILED)
        except Exception:
            pass
    finally:
        if db:
            await db.close()


async def _summarize_materials(materials: list[dict]) -> str:
    """
    分层摘要：对过长素材做分块摘要压缩

    流程：
    1. 按类型分组
    2. 每类素材分块（聊天记录按行切，其他按句子切）
    3. 逐块摘要
    4. 合并后如果还超长，做二次摘要
    """
    # 按类型分组
    by_type = {}
    for m in materials:
        t = m.get("type", "unknown")
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(m.get("content", ""))

    # 每类素材分别摘要
    summaries = []
    for t, contents in by_type.items():
        combined = "\n".join(contents)
        summary = await _summarize_single_type(t, combined)
        summaries.append(f"【{text_type_label(t)}】\n{summary}")

    result = "\n\n".join(summaries)

    # 如果合并后还超 3000 字，做二次摘要
    if len(result) > 3000:
        logger.info(f"合并摘要仍超长({len(result)}字)，做二次摘要")
        result = dashscope_client.chat(
            messages=[{"role": "user", "content": f"""请将以下多段摘要合并精炼为一段连贯的摘要，保留所有人格特征关键信息：

{result}

要求：
1. 合并为一段连贯的文字，不要分段
2. 保留说话风格、口头禅、性格、兴趣、价值观等关键信息
3. 控制在1500字以内
4. 直接输出摘要内容"""}],
            stream=False,
        )
        result = result.strip()

    return result


async def _summarize_single_type(source_type: str, content: str) -> str:
    """
    对单类素材做分块摘要

    - 聊天记录：按消息行分块
    - 其他类型：按句子边界分块
    """
    CHUNK_SIZE = 3000  # 每块最大字数
    SUMMARY_PER_CHUNK = 500  # 每块摘要目标字数

    # 如果内容不长，直接摘要
    if len(content) <= CHUNK_SIZE:
        return await _llm_summarize(content, source_type)

    # 分块
    chunks = _split_into_chunks(content, source_type, CHUNK_SIZE)
    logger.info(f"素材分块: type={source_type}, 总长={len(content)}字, 分为{len(chunks)}块")

    # 逐块摘要
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        summary = await _llm_summarize(chunk, source_type, chunk_index=i + 1, total_chunks=len(chunks))
        chunk_summaries.append(summary)

    # 合并所有块的摘要
    merged = "\n".join(chunk_summaries)

    # 如果合并后还超长，做二次压缩
    if len(merged) > CHUNK_SIZE:
        merged = dashscope_client.chat(
            messages=[{"role": "user", "content": f"""请将以下多段摘要合并精炼，保留所有人格特征关键信息：

{merged}

要求：
1. 合并为连贯的摘要
2. 保留说话风格、口头禅、性格特征等关键信息
3. 控制在{SUMMARY_PER_CHUNK}字以内
4. 直接输出摘要内容"""}],
            stream=False,
        )
        merged = merged.strip()

    return merged


def _split_into_chunks(text: str, source_type: str, max_chars: int) -> list[str]:
    """
    将文本分块

    - 聊天记录(chat_log)：按行分块，保持对话上下文
    - 其他类型：按句子边界分块
    """
    if source_type == "chat_log":
        return _split_by_lines(text, max_chars)
    else:
        return _split_by_sentences(text, max_chars)


def _split_by_lines(text: str, max_chars: int) -> list[str]:
    """
    按行分块（聊天记录专用）

    每行是一条消息，按行组装成块，不切断单条消息。
    """
    lines = text.splitlines()
    chunks = []
    current_chunk = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1  # +1 for newline
        if current_len + line_len > max_chars and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_len = line_len
        else:
            current_chunk.append(line)
            current_len += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks if chunks else [text[:max_chars]]


def _split_by_sentences(text: str, max_chars: int) -> list[str]:
    """
    按句子边界分块（爱好/习惯/描述等）

    在句号、问号、感叹号、换行处断句，不切断句子。
    """
    # 按句子拆分
    sentences = re.split(r'(?<=[。！？.!?\n])', text)
    sentences = [s for s in sentences if s.strip()]

    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        s_len = len(sentence)
        if current_len + s_len > max_chars and current_chunk:
            chunks.append("".join(current_chunk))
            current_chunk = [sentence]
            current_len = s_len
        else:
            current_chunk.append(sentence)
            current_len += s_len

    if current_chunk:
        chunks.append("".join(current_chunk))

    return chunks if chunks else [text[:max_chars]]


async def _llm_summarize(content: str, source_type: str, chunk_index: int = 1, total_chunks: int = 1) -> str:
    """调用LLM对单块内容做摘要"""
    label = text_type_label(source_type)
    chunk_hint = f"（第{chunk_index}/{total_chunks}部分）" if total_chunks > 1 else ""

    prompt = f"""请对以下{label}内容{chunk_hint}进行精炼摘要，提取关键的人格特征信息：

{content}

要求：
1. 保留说话风格、口头禅、性格特征、兴趣爱好、处事方式等关键信息
2. 如果是聊天记录，保留有代表性的对话片段作为例子
3. 摘要控制在500字以内
4. 直接输出摘要内容"""

    summary = dashscope_client.chat(
        messages=[{"role": "user", "content": prompt}],
        stream=False,
    )
    return summary.strip()


def _build_distill_prompt(name: str, description: str, materials: list[dict]) -> str:
    """构建蒸馏提示词（素材不长时直接用）"""
    # 按类型分组展示
    material_text = ""
    for m in materials:
        t = m.get("type", "unknown")
        content = m.get("content", "")
        material_text += f"\n### {text_type_label(t)}\n{content}\n"

    return f"""你是一位专业的人格分析师。请根据以下关于"{name}"的素材数据，生成一段完整的系统提示词。

这段系统提示词将用于让AI扮演{name}，模拟他的说话风格和性格来与用户对话。

## 关于{name}的信息
{description}

## {name}的原始素材
{material_text}

## 要求
请生成一段系统提示词，包含以下维度：
1. **身份设定**：你是{name}，一个真实存在的人
2. **说话风格**：语气、口头禅、常用表情、句式特点、正式程度
3. **性格特点**：主要性格特征、处事方式
4. **兴趣爱好**：喜欢的事物、话题
5. **价值观**：核心信念、人生态度
6. **情感表达**：情绪表达方式、支持他人的方式
7. **社交方式**：与朋友相处的模式

## 输出格式
直接输出系统提示词的正文，不要加代码块标记。系统提示词应该能让AI完全模拟{name}的人格来对话。

注意：
- 始终以{name}的第一人称视角
- 要具体、生动，不要泛泛而谈
- 如果素材中有具体的口头禅、表情习惯，一定要体现出来
- 末尾加上对话规则：保持人格一致性、不暴露是AI"""


def _build_distill_prompt_from_summary(name: str, description: str, summary: str) -> str:
    """构建蒸馏提示词（素材过长时用摘要版本）"""
    return f"""你是一位专业的人格分析师。请根据以下关于"{name}"的素材摘要，生成一段完整的系统提示词。

这段系统提示词将用于让AI扮演{name}，模拟他的说话风格和性格来与用户对话。

## 关于{name}的信息
{description}

## {name}的人格特征摘要
{summary}

## 要求
请生成一段系统提示词，包含以下维度：
1. **身份设定**：你是{name}，一个真实存在的人
2. **说话风格**：语气、口头禅、常用表情、句式特点、正式程度
3. **性格特点**：主要性格特征、处事方式
4. **兴趣爱好**：喜欢的事物、话题
5. **价值观**：核心信念、人生态度
6. **情感表达**：情绪表达方式、支持他人的方式
7. **社交方式**：与朋友相处的模式

## 输出格式
直接输出系统提示词的正文，不要加代码块标记。系统提示词应该能让AI完全模拟{name}的人格来对话。

注意：
- 始终以{name}的第一人称视角
- 要具体、生动，不要泛泛而谈
- 如果素材中有具体的口头禅、表情习惯，一定要体现出来
- 末尾加上对话规则：保持人格一致性、不暴露是AI"""


def _build_materials_text(materials: list[dict]) -> str:
    """将素材列表拼接为文本（素材不长时直接用）"""
    parts = []
    for m in materials:
        t = m.get("type", "unknown")
        content = m.get("content", "")
        parts.append(f"### {text_type_label(t)}\n{content}")
    return "\n\n".join(parts)


def _parse_json_array(text: str) -> list[dict]:
    """从 LLM 响应中解析 JSON 数组"""
    import re
    try:
        # 尝试提取 JSON 数组
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _default_calibration_questions(name: str) -> list[dict]:
    """默认校准问题（LLM 解析失败时的 fallback）"""
    return [
        {
            "id": 1,
            "question": f"{name}遇到压力或烦心事时，一般会怎么排解？",
            "options": ["打游戏/运动发泄", "找人吐槽倾诉", "自己扛着不说", "听音乐/看电影转移注意力"],
        },
        {
            "id": 2,
            "question": f"{name}安慰朋友的方式更接近哪种？",
            "options": ["帮忙出主意想办法", "陪着一起骂/吐槽", "默默陪伴不太会说", "转移话题逗对方开心"],
        },
        {
            "id": 3,
            "question": f"{name}和不熟的人相处时，通常是什么状态？",
            "options": ["很自来熟，很快能聊起来", "比较慢热，需要时间适应", "看情况，看对方是谁", "比较沉默，不太主动说话"],
        },
    ]


def text_type_label(t: str) -> str:
    """素材类型 → 中文标签"""
    labels = {
        "chat_log": "聊天记录",
        "moments": "朋友圈文字",
        "hobby": "爱好",
        "habit": "习惯",
        "description": "补充描述",
    }
    return labels.get(t, "素材")


async def _update_status(db: AsyncSession, friend_id: int, status: str):
    """更新数字朋友状态"""
    from sqlalchemy import update as sa_update
    await db.execute(
        sa_update(DigitalFriend)
        .where(DigitalFriend.id == friend_id)
        .values(status=status, update_time=datetime.now())
    )
    await db.commit()


def _to_response(friend: DigitalFriend) -> dict:
    """数字朋友 ORM → 响应字典"""
    result = {
        "friend_id": friend.id,
        "id": friend.id,
        "user_id": friend.user_id,
        "name": friend.name,
        "avatar_url": friend.avatar_url,
        "description": friend.description,
        "status": friend.status,
        "has_source_materials": bool(friend.source_materials),
        "has_system_prompt": bool(friend.system_prompt),
        "system_prompt": friend.system_prompt,
        "create_time": friend.create_time.strftime("%Y-%m-%d %H:%M:%S") if friend.create_time else "",
        "update_time": friend.update_time.strftime("%Y-%m-%d %H:%M:%S") if friend.update_time else "",
    }
    # 如果在校准阶段，返回校准信息
    if friend.status == STATUS_CALIBRATING:
        if friend.calibration_questions:
            result["calibration_questions"] = json.loads(friend.calibration_questions)
        if friend.calibration_answers:
            result["calibration_answers"] = json.loads(friend.calibration_answers)
    return result
