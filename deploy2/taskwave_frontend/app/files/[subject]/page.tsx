import Link from "next/link"
import { Folder, ChevronRight } from "lucide-react"
import { AppLayout } from "@/components/app-layout"

const months = [{ name: "8월", weeks: ["1주차", "2주차", "3주차", "4주차", "5주차"] }]

interface PageProps {
  params: {
    subject: string
  }
}

export default function SubjectPage({ params }: PageProps) {
  const subject = decodeURIComponent(params.subject)

  return (
    <AppLayout>
      {/* Breadcrumb */}
      <div className="px-6 py-2 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Link href="/files" className="hover:text-gray-900">
            파일 관리
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-gray-900">{subject}</span>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 px-6 py-8">
        <div className="max-w-4xl mx-auto">
          {months.map((month) => (
            <div key={month.name} className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">{month.name}</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                {month.weeks.map((week) => (
                  <Link
                    key={week}
                    href={`/files/${encodeURIComponent(subject)}/${encodeURIComponent(month.name)}/${encodeURIComponent(week)}`}
                    className="flex flex-col items-center p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all"
                  >
                    <Folder className="h-12 w-12 text-gray-600 mb-2" />
                    <span className="text-sm font-medium text-gray-900">{week}</span>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </main>
    </AppLayout>
  )
}
