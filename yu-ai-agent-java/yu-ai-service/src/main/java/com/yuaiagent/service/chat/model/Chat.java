package com.yuaiagent.service.chat.model;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 会话实体类
 */
@Data
@TableName("chat")
public class Chat {

    /**
     * 主键ID（自增）
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 会话ID（UUID格式）
     */
    private String chatId;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 应用类型：love_app | manus
     */
    private String appType;

    /**
     * 情感状态：single | relationship | married
     * 会话创建时设定，会话内不可更改
     */
    private String emotionStatus;

    /**
     * 会话标题
     */
    private String title;

    /**
     * 最后一条消息时间，用于会话列表排序
     */
    private LocalDateTime lastMessageTime;

    /**
     * 是否删除：0-未删除 1-已删除
     */
    @TableLogic
    private Integer isDeleted;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;

}
