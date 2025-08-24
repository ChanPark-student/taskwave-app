import Link from "next/link"
import { Folder, ChevronRight } from "lucide-react"
import { AppLayout } from "@/components/app-layout"

const days = ["9월 1일(월)", "9월 3일(수)"]

interface PageProps {
  params: {
    subject: string
    month: string
    week: string
  }
}

export default function WeekPage({ params }: PageProps) {
  const subject = decodeURIComponent(params.subject)
  const month = decodeURIComponent(params.month)
  const week = decodeURIComponent(params.week)

  return (
    <AppLayout>
      {/* Breadcrumb */}
      <div className="px-6 py-2 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Link href="/files" className="hover:text-gray-900">
            파일 관리
          </Link>
          <ChevronRight className="h-4 w-4" />
          <Link href={`/files/${encodeURIComponent(subject)}`} className="hover:text-gray-900">
            {subject}
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-gray-900">{week}</span>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 px-6 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            {days.map((day) => (
              <Link
                key={day}
                href={`/files/${encodeURIComponent(subject)}/${encodeURIComponent(month)}/${encodeURIComponent(week)}/${encodeURIComponent(day)}`}
                className="flex flex-col items-center p-6 bg-white rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all"
              >
                <Folder className="h-16 w-16 text-gray-600 mb-4" />
                <span className="text-sm font-medium text-gray-900">{day}</span>
              </Link>
            ))}
          </div>
        </div>
      </main>
    </AppLayout>
  )
}
