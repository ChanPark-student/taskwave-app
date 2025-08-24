import Link from "next/link"
import { Folder } from "lucide-react"
import { AppLayout } from "@/components/app-layout"

const subjects = ["인간공학", "물질공학", "대본동", "대백실", "심리학개론", "식품과 영양"]

export default function FilesPage() {
  return (
    <AppLayout>
      {/* Main Content */}
      <main className="flex-1 px-6 py-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-semibold text-gray-900 mb-8">파일 관리</h1>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            {subjects.map((subject) => (
              <Link
                key={subject}
                href={`/files/${encodeURIComponent(subject)}`}
                className="flex flex-col items-center p-6 bg-white rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all"
              >
                <Folder className="h-16 w-16 text-gray-600 mb-4" />
                <span className="text-sm font-medium text-gray-900">{subject}</span>
              </Link>
            ))}
          </div>
        </div>
      </main>
    </AppLayout>
  )
}
