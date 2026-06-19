package com.yuaiagent.service.chat.model;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 智能体任务实体类
 */
@Data
@TableName("agent_task")
public class AgentTask {

    /**
     * 主键ID（自增）
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 任务ID（UUID格式）
     */
    private String taskId;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 关联会话ID，Manus 类型通过此字段与 message 表关联
     */
    private String chatId;

    /**
     * 任务描述（用户输入的任务指令）
     */
    private String message;

    /**
     * 任务状态：pending | running | completed | failed | cancelled
     */
    private String status;

    /**
     * 任务最终结果
     */
    private String result;

    /**
     * 执行步骤详情（JSON格式）
     * Python 完成时一次性回写，取消任务时清空
     */
    private String steps;

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
