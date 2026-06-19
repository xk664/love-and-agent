package com.yuaiagent.service.user.service;

import com.yuaiagent.service.user.dto.LoginRequest;
import com.yuaiagent.service.user.dto.LoginResponse;
import com.yuaiagent.service.user.dto.RegisterRequest;
import com.yuaiagent.service.user.dto.RegisterResponse;
import com.yuaiagent.service.user.dto.UserInfoResponse;

/**
 * 用户服务接口
 */
public interface UserService {

    /**
     * 用户注册
     *
     * @param request 注册请求
     * @return 注册响应
     */
    RegisterResponse register(RegisterRequest request);

    /**
     * 用户登录
     *
     * @param request 登录请求
     * @return 登录响应（包含 Token 和用户信息）
     */
    LoginResponse login(LoginRequest request);



}
