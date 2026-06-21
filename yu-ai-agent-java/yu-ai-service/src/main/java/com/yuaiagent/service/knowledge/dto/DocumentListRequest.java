package com.yuaiagent.service.knowledge.dto;

import lombok.Data;

/**
 * 文档列表查询请求
 */
@Data
public class DocumentListRequest {

    /**
     * 页码
     */
    private Integer page = 1;

    /**
     * 每页数量
     */
    private Integer pageSize = 10;

}
