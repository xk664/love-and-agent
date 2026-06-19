package com.yuaiagent.common.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 分页响应封装
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class PageResponse<T> {

    /**
     * 数据列表
     */
    private List<T> list;

    /**
     * 分页信息
     */
    private Pagination pagination;

    /**
     * 分页信息
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Pagination {

        /**
         * 当前页码
         */
        private Integer page;

        /**
         * 每页数量
         */
        private Integer pageSize;

        /**
         * 总记录数
         */
        private Long total;

        /**
         * 总页数
         */
        private Integer totalPages;

    }

    /**
     * 创建分页响应
     */
    public static <T> PageResponse<T> of(List<T> list, Integer page, Integer pageSize, Long total) {
        Pagination pagination = new Pagination();
        pagination.setPage(page);
        pagination.setPageSize(pageSize);
        pagination.setTotal(total);
        pagination.setTotalPages((int) Math.ceil((double) total / pageSize));
        return new PageResponse<>(list, pagination);
    }

}
