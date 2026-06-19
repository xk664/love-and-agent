package com.yuaiagent.service.user.dto;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户注册响应
 */
@Data
public class RegisterResponse {

    /**
     * 用户ID
     */
    private Long id;

    /**
     * 用户名
     */
    private String username;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    public static RegisterResponse from(com.yuaiagent.service.user.model.User user) {
        RegisterResponse response = new RegisterResponse();
        response.setId(user.getId());
        response.setUsername(user.getUsername());
        response.setCreateTime(user.getCreateTime());
        return response;
    }
}
