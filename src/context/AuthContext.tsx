import { createContext, useState, useContext, ReactNode } from 'react';

// --- 타입(설명서) 정의 ---
interface User {
  name: string;
  school: string;
  dob: string;
}
interface Subject {
  name: string;
  days: number[];
}

// 파일 시스템의 구조를 구체적으로 정의합니다.
interface DayFolder {
  name: string;
  type: 'day-folder';
  files: any[]; // 파일 내부는 아직 구체화하지 않음
}
interface WeekFolder {
  [weekKey: string]: DayFolder[];
}
interface SubjectFolder {
  type: 'subject-folder';
  weeks: WeekFolder;
}
interface FileSystem {
  [subjectName: string]: SubjectFolder;
}

// AuthContext가 제공할 값들의 타입을 정의합니다.
interface AuthContextType {
  user: User | null;
  fileSystem: FileSystem; // 구체적인 FileSystem 타입 사용
  login: () => void;
  logout: () => void;
  updateProfile: (newProfile: User) => void;
}
// --- 타입 정의 끝 ---

const AuthContext = createContext<AuthContextType | null>(null);

// useAuth hook을 안전한 버전으로 수정합니다.
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

// --- 가짜 데이터 및 파일 생성 로직 ---
const sampleSubjects: Subject[] = [
  { name: '인간공학', days: [1, 3] },
  { name: '품질공학', days: [2, 4] },
  { name: '데분', days: [5] },
  { name: '캡스톤', days: [1, 3] },
  { name: '심리학개론', days: [2] },
  { name: '식품과영양', days: [4] },
];

const generateFilesForSubject = (subject: Subject): WeekFolder => { // 반환 타입을 WeekFolder로 명시
  const semesterStart = new Date('2025-09-01');
  const semesterEnd = new Date('2025-12-20');
  const weeklyFolders: WeekFolder = {};

  let currentDate = new Date(semesterStart);
  let weekCounter = 1;

  while (currentDate <= semesterEnd) {
    const dayOfWeek = currentDate.getDay();
    if (subject.days.includes(dayOfWeek)) {
      const weekKey = `${weekCounter}주차`;
      if (!weeklyFolders[weekKey]) {
        weeklyFolders[weekKey] = [];
      }
      const dateString = `${currentDate.getMonth() + 1}월 ${currentDate.getDate()}일(${['일','월','화','수','목','금','토'][dayOfWeek]})`;
      weeklyFolders[weekKey].push({ name: dateString, type: 'day-folder', files: [] });
    }
    currentDate.setDate(currentDate.getDate() + 1);
    if (dayOfWeek === 6) {
      weekCounter++;
    }
  }
  return weeklyFolders;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [fileSystem, setFileSystem] = useState<FileSystem>({}); // FileSystem 타입 사용

  const login = () => {
    setUser({
      name: '김구빈', school: '전남대학교', dob: '020314',
    });
    initializeFileSystem();
  };
  
  const logout = () => {
    setUser(null);
    setFileSystem({});
  };

  const updateProfile = (newProfile: User) => {
    setUser(newProfile);
  };

  const initializeFileSystem = () => {
    const newFileSystem: FileSystem = {};
    sampleSubjects.forEach(subject => {
      newFileSystem[subject.name] = {
        type: 'subject-folder',
        weeks: generateFilesForSubject(subject),
      };
    });
    setFileSystem(newFileSystem);
  };

  const value = {
    user,
    fileSystem,
    login,
    logout,
    updateProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};