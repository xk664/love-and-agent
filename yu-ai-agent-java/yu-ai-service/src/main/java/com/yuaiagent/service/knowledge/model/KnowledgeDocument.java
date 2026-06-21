package com.yuaiagent.service.knowledge.model;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 知识库文档实体类
 */
@Data
@TableName("knowledge_document")
public class KnowledgeDocument {

    /**
     * 主键ID（自增）
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 文档所属用户ID，实现用户隔离
     */
    private Long userId;

    /**
     * 文档标题，自动从上传文件名提取
     */
    private String title;

    /**
     * 文档内容，直接存储在数据库中
     */
    private String content;

    /**
     * 文件类型：markdown | pdf | txt
     */
    private String fileType;

    /**
     * 状态：0-待处理 1-已向量化 2-处理失败
     */
    private Integer status;

    /**
     * 是否删除：0-未删除 1-已删除
     */
    @TableLogic
    private Integer isDeleted;

    /**
     * 向量是否已清理：0-未清理 1-已清理
     */
    private Integer vectorDeleted;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;

}
