package com.yuaiagent.service.chat.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yuaiagent.service.chat.model.Chat;
import org.apache.ibatis.annotations.Mapper;

/**
 * 会话 Mapper 接口
 */
@Mapper
public interface ChatMapper extends BaseMapper<Chat> {

}
