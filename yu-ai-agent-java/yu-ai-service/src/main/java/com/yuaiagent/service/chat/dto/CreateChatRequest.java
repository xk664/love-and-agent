package com.yuaiagent.service.chat.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

/**
 * 创建会话请求
 */
@Data
public class CreateChatRequest {

    /**
     * 应用类型：love_app | manus
     */
    @NotBlank(message = "应用类型不能为空")
    @Pattern(regexp = "^(love_app|manus)$", message = "应用类型必须为 love_app 或 manus")
    private String appType;

    /**
     * 情感状态：single | relationship | married
     * love_app 时必填，manus 时忽略
     */
    @Pattern(regexp = "^(single|relationship|married)$", message = "情感状态必须为 single、relationship 或 married")
    private String emotionStatus;

    /**
     * 会话标题（可选）
     */
    private String title;

}
