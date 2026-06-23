package com.yuaiagent.service.user.controller;

import com.yuaiagent.common.response.Result;
import com.yuaiagent.service.user.dto.LoginRequest;
import com.yuaiagent.service.user.dto.LoginResponse;
import com.yuaiagent.service.user.dto.RegisterRequest;
import com.yuaiagent.service.user.dto.RegisterResponse;
import com.yuaiagent.service.user.dto.UserInfoResponse;
import com.yuaiagent.service.user.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 用户控制器
 */
@Tag(name = "用户", description = "用户注册、登录、信息管理")
@RestController
@RequestMapping("/api/v1/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    /**
     * 用户注册
     */
    @Operation(summary = "用户注册")
    @PostMapping("/register")
    public Result<RegisterResponse> register(@RequestBody RegisterRequest request) {
        RegisterResponse response = userService.register(request);
        return Result.success(response);
    }

    /**
     * 用户登录
     */
    @Operation(summary = "用户登录")
    @PostMapping("/login")
    public Result<LoginResponse> login(@RequestBody LoginRequest request) {
        LoginResponse response = userService.login(request);
        return Result.success(response);
    }

    /**
     * 获取当前用户信息
     */
    @Operation(summary = "获取当前用户信息")
    @GetMapping("/info")
    public Result<UserInfoResponse> getUserInfo(@RequestAttribute("currentUserId") Long userId) {
        UserInfoResponse response = userService.getUserInfo(userId);
        return Result.success(response);
    }

}
