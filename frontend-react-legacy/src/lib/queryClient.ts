import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // 30s 内不重复请求
      gcTime: 5 * 60_000, // 5 分钟 GC
      retry: (failureCount, error) => {
        // 401/403 不重试
        if (
          error &&
          typeof error === "object" &&
          "status" in error &&
          (error.status === 401 || error.status === 403 || error.status === 404)
        ) {
          return false;
        }
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
    },
  },
});
