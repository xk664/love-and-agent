package com.yuaiagent.common.config;

import com.yuaiagent.common.utils.JwtUtils;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.Arrays;
import java.util.List;

/**
 * JWT 认证拦截器
 * 验证 Token 有效性，提取用户ID到 request attribute
 */
@Slf4j
@Component
public class JwtAuthInterceptor implements HandlerInterceptor {

    @Value("${jwt.secret:yu-ai-agent-java-default-secret-key-must-be-at-least-256-bits-long}")
    private String jwtSecret;

    private static final String HEADER_AUTHORIZATION = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";
    public static final String REQUEST_USER_ID = "currentUserId";
    public static final String REQUEST_USERNAME = "currentUsername";

    /**
     * 排除认证的路径列表
     */
    private static final List<String> EXCLUDE_PATHS = Arrays.asList(
            "/api/v1/user/register",
            "/api/v1/user/login",
            "/api/v1/internal/**",
            "/api/health",
            "/swagger-ui/**",
            "/v3/api-docs/**",
            "/doc.html",
            "/webjars/**"
    );

    private final AntPathMatcher pathMatcher = new AntPathMatcher();

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        String path = request.getRequestURI();

        // 检查是否是需要排除的路径
        if (isExcludePath(path)) {
            return true;
        }

        // 获取 Authorization 头
        String authHeader = request.getHeader(HEADER_AUTHORIZATION);

        // 检查 Token 是否存在
        if (!StringUtils.hasText(authHeader) || !authHeader.startsWith(BEARER_PREFIX)) {
            log.warn("请求路径 {} 缺少有效的 Authorization 头", path);
            sendUnauthorized(response, "未提供认证Token");
            return false;
        }

        // 提取 Token
        String token = authHeader.substring(BEARER_PREFIX.length());

        try {
            // 验证 Token
            Claims claims = JwtUtils.parseToken(token);

            // 提取用户ID
            Long userId = claims.get("userId", Long.class);
            String username = claims.get("username", String.class);

            if (userId == null) {
                log.warn("Token中缺少用户ID");
                sendUnauthorized(response, "Token无效");
                return false;
            }

            // 设置到 request attribute，Controller 可通过 @RequestAttribute 获取
            request.setAttribute(REQUEST_USER_ID, userId);
            request.setAttribute(REQUEST_USERNAME, username);

            log.debug("JWT认证成功，用户ID: {}，路径: {}", userId, path);
            return true;

        } catch (ExpiredJwtException e) {
            log.warn("Token已过期，路径: {}", path);
            sendUnauthorized(response, "Token已过期，请重新登录");
        } catch (JwtException e) {
            log.warn("Token验证失败: {}，路径: {}", e.getMessage(), path);
            sendUnauthorized(response, "Token无效");
        } catch (Exception e) {
            log.error("JWT认证异常: {}", e.getMessage(), e);
            sendUnauthorized(response, "认证失败");
        }

        return false;
    }

    /**
     * 判断是否是排除认证的路径
     */
    private boolean isExcludePath(String path) {
        return EXCLUDE_PATHS.stream()
                .anyMatch(pattern -> pathMatcher.match(pattern, path));
    }

    /**
     * 返回 401 未认证响应
     */
    private void sendUnauthorized(HttpServletResponse response, String message) throws Exception {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        String body = String.format(
                "{\"code\":401,\"message\":\"%s\",\"data\":null}",
                message
        );
        response.getWriter().write(body);
    }
}
