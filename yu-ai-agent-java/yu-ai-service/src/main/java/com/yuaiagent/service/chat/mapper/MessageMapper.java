package com.yuaiagent.service.chat.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yuaiagent.service.chat.model.Message;
import org.apache.ibatis.annotations.Mapper;

/**
 * 消息 Mapper 接口
 */
@Mapper
public interface MessageMapper extends BaseMapper<Message> {

}
