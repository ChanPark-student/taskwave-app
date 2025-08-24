const timeSlots = ["9", "10", "11", "12", "1", "2", "3"]

const days = ["월", "화", "수", "목", "금"]

const scheduleData = {
  월: {
    "10": { subject: "데이터베이스", code: "31A-312", color: "bg-green-200" },
    "11": { subject: "인간공학", code: "31A-313", color: "bg-red-200" },
    "1": { subject: "공업경영", code: "31A-312", color: "bg-yellow-200" },
    "2": { subject: "신뢰성개론", code: "시뮬레이션실습", color: "bg-blue-200" },
    "3": { subject: "신뢰성개론", code: "31A100", color: "bg-orange-200" },
  },
  화: {
    "10": { subject: "데이터베이스", code: "31A-312", color: "bg-green-200" },
    "11": { subject: "인간공학", code: "31A-313", color: "bg-red-200" },
    "1": { subject: "공업경영", code: "31A-312", color: "bg-yellow-200" },
    "2": { subject: "신뢰성개론", code: "시뮬레이션실습", color: "bg-blue-200" },
    "3": { subject: "신뢰성개론", code: "31A100", color: "bg-orange-200" },
  },
  수: {
    "10": { subject: "데이터베이스", code: "31A-312", color: "bg-green-200" },
    "11": { subject: "인간공학", code: "31A-313", color: "bg-red-200" },
  },
  목: {
    "10": { subject: "데이터베이스", code: "31A-312", color: "bg-green-200" },
    "11": { subject: "인간공학", code: "31A-313", color: "bg-red-200" },
  },
  금: {
    "1": { subject: "공업경영", code: "31A-312", color: "bg-yellow-200" },
    "2": { subject: "신뢰성개론", code: "시뮬레이션실습", color: "bg-blue-200" },
  },
}

export function Timetable() {
  return (
    <div className="overflow-x-auto">
      <div className="min-w-[600px]">
        {/* Header */}
        <div className="grid grid-cols-6 gap-1 mb-2">
          <div className="p-2 text-center text-sm font-medium text-gray-700"></div>
          {days.map((day) => (
            <div key={day} className="p-2 text-center text-sm font-medium text-gray-700 bg-gray-100 rounded">
              {day}
            </div>
          ))}
        </div>

        {/* Time slots */}
        {timeSlots.map((time) => (
          <div key={time} className="grid grid-cols-6 gap-1 mb-1">
            <div className="p-2 text-center text-sm font-medium text-gray-700 bg-gray-100 rounded">{time}</div>
            {days.map((day) => {
              const schedule = scheduleData[day as keyof typeof scheduleData]?.[time]
              return (
                <div
                  key={`${day}-${time}`}
                  className={`p-2 rounded text-xs ${
                    schedule ? `${schedule.color} border border-gray-300` : "bg-white border border-gray-200"
                  }`}
                >
                  {schedule && (
                    <div className="text-center">
                      <div className="font-medium text-gray-800">{schedule.subject}</div>
                      <div className="text-gray-600">{schedule.code}</div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
