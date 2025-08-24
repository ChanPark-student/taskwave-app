"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Mountain, Eye, EyeOff } from "lucide-react"
import { authApi } from "@/lib/api"

export default function SignupPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
  // 1) 회원가입 (이메일+비번; name은 내부에서 email 아이디로 자동 생성)
  const reg = await authApi.register(email, password);
  if (reg.error || !reg.data) {
    setError(reg.error ?? "회원가입에 실패했습니다.");
    return;
  }

  // 2) 안전장치: 회원가입에서 토큰 저장이 실패했다면 로그인 한 번 더 시도
  let token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (!token) {
    const login = await authApi.login(email, password);
    if (login.error || !login.data) {
      // 로그인도 실패하면 로그인 페이지로 유도
      setError(login.error ?? "로그인에 실패했습니다.");
      router.push("/login");
      return;
    }
    token = login.data.access_token;
  }

  // 3) 성공 → 대시보드로
  router.push("/dashboard");
} catch (e: any) {
  // FastAPI 422 등 detail 객체가 와도 문자열로만 노출되도록
  setError(e?.message ?? "알 수 없는 오류가 발생했습니다.");
} finally {
  setIsLoading(false);
}
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6">
      {/* Logo */}
      <div className="flex items-center gap-2 mb-12">
        <Mountain className="h-8 w-8 text-green-700" />
        <span className="text-2xl font-semibold text-gray-900">Taskwave</span>
      </div>

      {/* Signup Form */}
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-semibold text-center text-gray-900 mb-8">회원가입</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">{error}</div>}

          <div>
            <Label htmlFor="email" className="text-sm font-medium text-gray-700">
              이메일 입력
            </Label>
            <Input
              id="email"
              type="email"
              placeholder="email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1"
              required
            />
          </div>

          <div>
            <Label htmlFor="password" className="text-sm font-medium text-gray-700">
              암호 입력
            </Label>
            <div className="relative mt-1">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="암호 입력"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pr-10"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <Button type="submit" className="w-full bg-green-700 hover:bg-green-800" disabled={isLoading}>
            {isLoading ? "가입 중..." : "회원가입"}
          </Button>
        </form>

        <p className="text-center text-sm text-gray-600 mt-6">
          이미 계정이 있으신가요?{" "}
          <Link href="/login" className="text-green-700 hover:text-green-800 font-medium">
            로그인
          </Link>
        </p>
      </div>
    </div>
  )
}
