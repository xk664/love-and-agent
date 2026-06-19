package com.yuaiagent.service.user.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yuaiagent.common.exception.BusinessException;
import com.yuaiagent.common.utils.JwtUtils;
import com.yuaiagent.service.user.dto.LoginRequest;
import com.yuaiagent.service.user.dto.LoginResponse;
import com.yuaiagent.service.user.dto.RegisterRequest;
import com.yuaiagent.service.user.dto.RegisterResponse;
import com.yuaiagent.service.user.dto.UserInfoResponse;
import com.yuaiagent.service.user.mapper.UserMapper;
import com.yuaiagent.service.user.model.User;
import com.yuaiagent.service.user.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

/**
 * 用户服务实现
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;

    private static final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    @Override
    public RegisterResponse register(RegisterRequest request) {
        // 1. 用户名唯一性校验
        checkUsernameUnique(request.getUsername());

        // 2. 创建用户
        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setStatus(1);
        user.setIsDeleted(0);
        user.setCreateTime(LocalDateTime.now());
        user.setUpdateTime(LocalDateTime.now());

        // 3. 保存到数据库
        userMapper.insert(user);

        log.info("用户注册成功，用户ID: {}, 用户名: {}", user.getId(), user.getUsername());

        // 4. 返回响应
        return RegisterResponse.from(user);
    }

    @Override
    public LoginResponse login(LoginRequest request) {
        // 1. 根据用户名查询用户
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(User::getUsername, request.getUsername());
        User user = userMapper.selectOne(wrapper);

        // 2. 校验用户是否存在
        if (user == null) {
            throw new BusinessException(400, "用户名或密码错误");
        }

        // 3. 校验用户状态
        if (user.getStatus() == 0) {
            throw new BusinessException(403, "用户已被禁用");
        }

        // 4. 校验密码
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BusinessException(400, "用户名或密码错误");
        }

        // 5. 生成 JWT Token
        String token = JwtUtils.generateToken(user.getId(), user.getUsername());

        log.info("用户登录成功，用户ID: {}, 用户名: {}", user.getId(), user.getUsername());

        // 6. 返回响应
        return LoginResponse.from(token, user);
    }

    /**
     * 校验用户名唯一性
     */
    private void checkUsernameUnique(String username) {
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(User::getUsername, username);
        Long count = userMapper.selectCount(wrapper);
        if (count > 0) {
            throw new BusinessException(400, "用户名已存在");
        }
    }
}
