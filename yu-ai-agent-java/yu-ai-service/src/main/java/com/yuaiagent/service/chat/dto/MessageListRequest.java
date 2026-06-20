package com.yuaiagent.service.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;

/**
 * 消息列表查询请求
 */
@Data
public class MessageListRequest {

    /**
     * 页码（默认1）
     */
    @Min(value = 1, message = "页码最小为1")
    private Integer page = 1;

    /**
     * 每页数量（默认20，最大100）
     */
    @Min(value = 1, message = "每页数量最小为1")
    @Max(value = 100, message = "每页数量最大为100")
    @JsonProperty("page_size")
    private Integer pageSize = 20;

}
