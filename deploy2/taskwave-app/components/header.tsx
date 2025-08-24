"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Mountain, User, Settings, LogOut, FileText } from "lucide-react"

export function Header() {
  const handleLogout = () => {
    // TODO: Implement actual logout logic
    console.log("Logging out...")
    window.location.href = "/"
  }

  return (
    <header className="flex justify-between items-center p-6 bg-white border-b border-gray-200">
      <Link href="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
        <Mountain className="h-6 w-6 text-green-700" />
        <span className="text-xl font-semibold text-gray-900">Taskwave</span>
      </Link>

      <div className="flex items-center gap-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="rounded-full">
              <User className="h-5 w-5 text-green-700" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem asChild>
              <Link href="/profile" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />내 계정
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/files" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                파일 관리
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="flex items-center gap-2 text-red-600">
              <LogOut className="h-4 w-4" />
              로그아웃
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
