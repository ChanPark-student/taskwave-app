import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Upload, Mountain } from "lucide-react"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="flex justify-between items-center p-6">
        <div className="flex items-center gap-2">
          <Mountain className="h-6 w-6 text-green-700" />
          <span className="text-xl font-semibold text-gray-900">Taskwave</span>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" asChild>
            <Link href="/login">로그인</Link>
          </Button>
          <Button asChild className="bg-green-700 hover:bg-green-800">
            <Link href="/signup">회원가입</Link>
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-2xl">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-16 text-center bg-white">
            <h2 className="text-2xl font-semibold text-gray-900 mb-8">파일 업로드</h2>

            <div className="mb-8">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-4">
                <Upload className="h-10 w-10 text-green-700" />
              </div>
              <p className="text-gray-600 mb-2">여기에 PDF 파일 놓기</p>
              <p className="text-sm text-gray-400">또는</p>
            </div>

            <Button className="bg-green-700 hover:bg-green-800 px-8">업로드하여 편집</Button>
          </div>
        </div>
      </main>
    </div>
  )
}
