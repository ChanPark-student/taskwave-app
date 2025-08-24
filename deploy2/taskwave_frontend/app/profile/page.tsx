"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Upload } from "lucide-react"
import { Timetable } from "@/components/timetable"
import { AppLayout } from "@/components/app-layout"
import { userApi, scheduleApi } from "@/lib/api"

export default function ProfilePage() {
  const [hasUploadedTimetable, setHasUploadedTimetable] = useState(false)
  const [userProfile, setUserProfile] = useState({
    name: "김구민",
    school: "전남대학교",
    birthDate: "020314",
  })
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState("")

  useEffect(() => {
    const loadProfile = async () => {
      const result = await userApi.getProfile()
      if (result.data) {
        setUserProfile({
          name: result.data.name || "김구민",
          school: result.data.school || "전남대학교",
          birthDate: result.data.birth_date || "020314",
        })
      }
    }
    loadProfile()
  }, [])

  const handleTimetableUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setUploadError("")

    const result = await scheduleApi.uploadSchedule(file)

    if (result.data) {
      setHasUploadedTimetable(true)
    } else {
      setUploadError(result.error || "시간표 업로드에 실패했습니다.")
    }

    setIsUploading(false)
  }

  return (
    <AppLayout>
      {/* Main Content */}
      <main className="flex-1 px-6 py-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl font-semibold text-gray-900 mb-8">내 계정</h1>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Profile Information */}
            <div className="bg-white rounded-lg p-6 border border-gray-200">
              <div className="flex justify-between items-start mb-6">
                <h2 className="text-lg font-semibold text-gray-900">프로필</h2>
                <Button variant="outline" size="sm">
                  변경
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <span className="text-sm font-medium text-gray-700">성명: </span>
                  <span className="text-sm text-gray-900">{userProfile.name}</span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-700">학교: </span>
                  <span className="text-sm text-gray-900">{userProfile.school}</span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-700">생년월일: </span>
                  <span className="text-sm text-gray-900">{userProfile.birthDate}</span>
                </div>
              </div>
            </div>

            {/* Timetable Upload/Display */}
            <div className="bg-white rounded-lg border border-gray-200">
              {!hasUploadedTimetable ? (
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <h3 className="text-lg font-semibold text-gray-900 mb-6">시간표 업로드</h3>

                  {uploadError && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
                      {uploadError}
                    </div>
                  )}

                  <div className="mb-6">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
                      <Upload className="h-8 w-8 text-green-700" />
                    </div>
                    <p className="text-gray-600 mb-2">여기에 PDF 파일 놓기</p>
                    <p className="text-sm text-gray-400">또는</p>
                  </div>

                  <div>
                    <input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg,.webp"
                      onChange={handleTimetableUpload}
                      className="hidden"
                      id="timetable-upload"
                    />
                    <Button
                      onClick={() => document.getElementById("timetable-upload")?.click()}
                      className="bg-green-700 hover:bg-green-800"
                      disabled={isUploading}
                    >
                      {isUploading ? "업로드 중..." : "업로드하여 편집"}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">시간표</h3>
                  <Timetable />
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </AppLayout>
  )
}
