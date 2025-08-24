"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Upload } from "lucide-react"
import { AppLayout } from "@/components/app-layout"
import { uploadApi } from "@/lib/api"

export default function DashboardPage() {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState("")

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setUploadError("")

    const result = await uploadApi.uploadFile(file, {
      type: "general",
      category: "document",
    })

    if (result.data) {
      // Handle successful upload
      console.log("File uploaded successfully:", result.data)
    } else {
      setUploadError(result.error || "파일 업로드에 실패했습니다.")
    }

    setIsUploading(false)
  }

  return (
    <AppLayout>
      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="w-full max-w-2xl">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-16 text-center bg-white">
            <h2 className="text-2xl font-semibold text-gray-900 mb-8">파일 업로드</h2>

            {uploadError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">{uploadError}</div>
            )}

            <div className="mb-8">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-4">
                <Upload className="h-10 w-10 text-green-700" />
              </div>
              <p className="text-gray-600 mb-2">여기에 PDF 파일 놓기</p>
              <p className="text-sm text-gray-400">또는</p>
            </div>

            <div className="space-y-4">
              <div>
                <input type="file" accept=".pdf" onChange={handleFileUpload} className="hidden" id="file-upload" />
                <Button
                  className="bg-green-700 hover:bg-green-800 px-8"
                  onClick={() => document.getElementById("file-upload")?.click()}
                  disabled={isUploading}
                >
                  {isUploading ? "업로드 중..." : "업로드하여 편집"}
                </Button>
              </div>
              <div>
                <Button variant="outline" asChild>
                  <Link href="/files">파일 관리</Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </AppLayout>
  )
}
