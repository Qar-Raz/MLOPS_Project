import Link from 'next/link';
import { GithubButton } from '@/components/ui/github-button'; // Importing your new component

export default function Header() {
  return (
    <header className="absolute top-0 left-0 z-20 w-full p-4 md:p-6">
      <nav className="mx-auto flex max-w-7xl items-center justify-between">

        {/* Left Side -- Name of Project  */}
        <Link href="/" className="text-xl font-bold tracking-wider text-white transition-colors hover:text-gray-200">
          Fluora Care
        </Link>

        {/* Right Side --  Github link */}
        <GithubButton
          // see https://reui.io/docs/github-button for more variables
          initialStars={1}
          label=""
          targetStars={5}

          repoUrl="https://github.com/Qar-Raz/mlops_project.git"

          filled = {true}
          animationDuration= {5}
          roundStars={true}
          // below line can be commented out for clear black button --@Qamar
          className="bg-gray-900/50 border-gray-700 text-gray-200 hover:bg-gray-800/50 hover:border-gray-600"
        />

      </nav>
    </header>
  );
}
