# TypeScript/React Standards

## 🎯 Core Principles

1. **TypeScript strict mode** - No implicit any
2. **Functional components only** - No class components
3. **Server Components by default** - Use 'use client' sparingly
4. **Tailwind for styling** - No separate CSS files
5. **Accessibility first** - ARIA labels, keyboard navigation

---

## 📝 File Template

```typescript
// File: packages/web-ui/components/TaskCard.tsx

'use client'  // Only if using hooks/browser APIs

import { useState } from 'react'
import { cn } from '@/lib/utils'

/**
 * Task card component.
 * 
 * Displays a single task with status, progress, and actions.
 * 
 * @example
 * <TaskCard
 *   taskId="123"
 *   title="Generate API"
 *   status="running"
 *   progress={45}
 * />
 */

// Props interface BEFORE component
interface TaskCardProps {
  taskId: string
  title: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress?: number  // Optional with ?
  onRetry?: () => void
  className?: string
}

export default function TaskCard({
  taskId,
  title,
  status,
  progress = 0,  // Default value
  onRetry,
  className
}: TaskCardProps) {
  // Hooks at top
  const [isExpanded, setIsExpanded] = useState(false)
  
  // Event handlers: handle* naming
  const handleToggle = () => {
    setIsExpanded(!isExpanded)
  }
  
  const handleRetry = () => {
    if (onRetry) {
      onRetry()
    }
  }
  
  // Derived state
  const statusColor = {
    pending: 'bg-gray-500',
    running: 'bg-blue-500',
    completed: 'bg-green-500',
    failed: 'bg-red-500'
  }[status]
  
  return (
    <div className={cn(
      'bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow',
      className
    )}>
      {/* Status badge */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold">{title}</h3>
        <span className={cn(
          'px-2 py-1 rounded text-xs text-white',
          statusColor
        )}>
          {status}
        </span>
      </div>
      
      {/* Progress bar */}
      {status === 'running' && (
        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      )}
      
      {/* Actions */}
      <div className="flex gap-2 mt-4">
        <button
          onClick={handleToggle}
          className="text-sm text-blue-600 hover:text-blue-800"
          aria-expanded={isExpanded}
        >
          {isExpanded ? 'Hide Details' : 'Show Details'}
        </button>
        
        {status === 'failed' && onRetry && (
          <button
            onClick={handleRetry}
            className="text-sm text-red-600 hover:text-red-800"
          >
            Retry
          </button>
        )}
      </div>
      
      {/* Expanded content */}
      {isExpanded && (
        <div className="mt-4 p-3 bg-gray-50 rounded">
          <p className="text-sm text-gray-600">
            Task ID: {taskId}
          </p>
        </div>
      )}
    </div>
  )
}
```

---

## 🏗️ Project Structure

packages/web-ui/
├── app/                        # Next.js App Router
│   ├── layout.tsx             # Root layout
│   ├── page.tsx               # Home page
│   ├── dashboard/
│   │   ├── page.tsx           # Dashboard page
│   │   └── layout.tsx         # Dashboard layout
│   ├── tasks/
│   │   ├── page.tsx           # Tasks list
│   │   └── [id]/
│   │       └── page.tsx       # Task detail
│   └── api/                   # API routes
│       └── stream/
│           └── route.ts       # SSE endpoint
│
├── components/                # React components
│   ├── ui/                    # Shadcn/UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── ...
│   ├── TaskCard.tsx
│   ├── TaskQueue.tsx
│   ├── CodePreview.tsx
│   └── ...
│
├── lib/                       # Utilities
│   ├── utils.ts               # Helper functions
│   ├── api.ts                 # API client
│   └── supabase.ts            # Supabase client
│
├── hooks/                     # Custom hooks
│   ├── useTask.ts
│   ├── useRealtime.ts
│   └── ...
│
├── types/                     # TypeScript types
│   ├── task.ts
│   ├── project.ts
│   └── ...
│
├── public/                    # Static files
│   ├── logo.svg
│   └── ...
│
├── styles/
│   └── globals.css            # Tailwind imports
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js

---

## 📦 Dependencies (package.json)

```json
{
  "name": "codeagent-web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "15.0.0",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    
    "@supabase/supabase-js": "^2.39.0",
    "@monaco-editor/react": "^4.6.0",
    
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",
    
    "lucide-react": "^0.309.0",
    "date-fns": "^3.0.6"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    
    "typescript": "^5.3.3",
    "eslint": "^8.56.0",
    "eslint-config-next": "15.0.0",
    
    "tailwindcss": "^3.4.1",
    "postcss": "^8.4.33",
    "autoprefixer": "^10.4.16",
    
    "@tailwindcss/typography": "^0.5.10",
    "@tailwindcss/forms": "^0.5.7"
  }
}
```

---

## 🎨 TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,  // REQUIRED
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    },
    
    // Strict type checking
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

---

## 🎯 Next.js App Router Patterns

### Server Component (Default)

```typescript
// app/dashboard/page.tsx

import { createServerComponentClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import TaskList from '@/components/TaskList'

// This is a Server Component (no 'use client')
export default async function DashboardPage() {
  // Data fetching on server
  const supabase = createServerComponentClient({ cookies })
  
  const { data: tasks } = await supabase
    .from('tasks')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(10)
  
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      
      {/* Pass data to Client Component */}
      <TaskList initialTasks={tasks || []} />
    </div>
  )
}

// TypeScript metadata
export const metadata = {
  title: 'Dashboard | CodeAgent',
  description: 'Manage your coding tasks'
}
```

### Client Component (Interactive)

```typescript
// components/TaskList.tsx

'use client'  // Required for hooks

import { useState, useEffect } from 'react'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import type { Task } from '@/types/task'

interface TaskListProps {
  initialTasks: Task[]
}

export default function TaskList({ initialTasks }: TaskListProps) {
  const [tasks, setTasks] = useState<Task[]>(initialTasks)
  const supabase = createClientComponentClient()
  
  useEffect(() => {
    // Subscribe to realtime updates
    const channel = supabase
      .channel('tasks')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'tasks' },
        (payload) => {
          // Handle realtime updates
          if (payload.eventType === 'INSERT') {
            setTasks(prev => [payload.new as Task, ...prev])
          }
        }
      )
      .subscribe()
    
    return () => {
      supabase.removeChannel(channel)
    }
  }, [supabase])
  
  return (
    <div className="space-y-4">
      {tasks.map(task => (
        <TaskCard key={task.id} task={task} />
      ))}
    </div>
  )
}
```

### API Route (Server-Sent Events)

```typescript
// app/api/stream/route.ts

import { NextRequest } from 'next/server'

export async function GET(request: NextRequest) {
  const taskId = request.nextUrl.searchParams.get('taskId')
  
  // Create readable stream
  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder()
      
      // Send updates
      const sendUpdate = (data: any) => {
        const message = `data: ${JSON.stringify(data)}\n\n`
        controller.enqueue(encoder.encode(message))
      }
      
      // Simulate agent progress
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 1000))
        sendUpdate({ progress: i, step: `Step ${i/10}` })
      }
      
      controller.close()
    }
  })
  
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}
```

---

## 🎨 Tailwind CSS Patterns

```typescript
// Good: Utility classes inline
<div className="flex items-center justify-between p-4 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">
  <h2 className="text-xl font-semibold">Title</h2>
  <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
    Click
  </button>
</div>

// Good: Conditional classes with cn()
import { cn } from '@/lib/utils'

const buttonClass = cn(
  'px-4 py-2 rounded font-medium',
  variant === 'primary' && 'bg-blue-600 text-white',
  variant === 'secondary' && 'bg-gray-200 text-gray-900',
  isLoading && 'opacity-50 cursor-not-allowed'
)

// Good: Responsive design
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Mobile: 1 column, Tablet: 2 columns, Desktop: 3 columns */}
</div>

// Bad: Separate CSS file
// ❌ Don't create styles.css
```

### Dark Mode Support

```typescript
// tailwind.config.ts
module.exports = {
  darkMode: 'class',  // Enable dark mode
  theme: {
    extend: {
      colors: {
        // Define semantic colors
        background: 'var(--background)',
        foreground: 'var(--foreground)',
      }
    }
  }
}

// globals.css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
  }
  
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
  }
}

// Component usage
<div className="bg-background text-foreground">
  {/* Automatically switches with dark mode */}
</div>
```

---

## 🪝 Custom Hooks

```typescript
// hooks/useTask.ts

import { useState, useEffect } from 'react'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import type { Task } from '@/types/task'

/**
 * Hook to manage single task with realtime updates.
 * 
 * @example
 * const { task, loading, error } = useTask(taskId)
 */
export function useTask(taskId: string) {
  const [task, setTask] = useState<Task | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  
  const supabase = createClientComponentClient()
  
  useEffect(() => {
    // Fetch initial data
    const fetchTask = async () => {
      try {
        const { data, error } = await supabase
          .from('tasks')
          .select('*')
          .eq('id', taskId)
          .single()
        
        if (error) throw error
        
        setTask(data)
      } catch (err) {
        setError(err as Error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchTask()
    
    // Subscribe to updates
    const channel = supabase
      .channel(`task:${taskId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'tasks',
          filter: `id=eq.${taskId}`
        },
        (payload) => {
          setTask(payload.new as Task)
        }
      )
      .subscribe()
    
    return () => {
      supabase.removeChannel(channel)
    }
  }, [taskId, supabase])
  
  return { task, loading, error }
}
```

---

## 🧪 Testing (Jest + React Testing Library)

```typescript
// components/__tests__/TaskCard.test.tsx

import { render, screen, fireEvent } from '@testing-library/react'
import TaskCard from '../TaskCard'

describe('TaskCard', () => {
  it('renders task title and status', () => {
    render(
      <TaskCard
        taskId="123"
        title="Test Task"
        status="running"
        progress={50}
      />
    )
    
    expect(screen.getByText('Test Task')).toBeInTheDocument()
    expect(screen.getByText('running')).toBeInTheDocument()
  })
  
  it('shows retry button when failed', () => {
    const onRetry = jest.fn()
    
    render(
      <TaskCard
        taskId="123"
        title="Failed Task"
        status="failed"
        onRetry={onRetry}
      />
    )
    
    const retryButton = screen.getByText('Retry')
    fireEvent.click(retryButton)
    
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
  
  it('displays progress bar when running', () => {
    render(
      <TaskCard
        taskId="123"
        title="Running Task"
        status="running"
        progress={75}
      />
    )
    
    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toHaveAttribute('aria-valuenow', '75')
  })
})
```

---

## ♿ Accessibility

```typescript
// Good: Semantic HTML + ARIA
<button
  onClick={handleClick}
  aria-label="Delete task"
  aria-describedby="delete-tooltip"
>
  <TrashIcon className="w-4 h-4" />
</button>

<div id="delete-tooltip" className="sr-only">
  This action cannot be undone
</div>

// Good: Keyboard navigation
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick()
    }
  }}
>
  Click me
</div>

// Good: Form labels
<label htmlFor="task-name" className="block mb-2">
  Task Name
</label>
<input
  id="task-name"
  type="text"
  className="w-full px-3 py-2 border rounded"
  aria-required="true"
/>

// Good: Error messages
<input
  type="email"
  aria-invalid={!!error}
  aria-describedby="email-error"
/>
{error && (
  <p id="email-error" className="text-red-600 text-sm mt-1" role="alert">
    {error}
  </p>
)}
```

---

## 🚫 Anti-Patterns (AVOID)

```typescript
// ❌ Class components
class TaskCard extends React.Component {
  render() { ... }
}

// ✅ Functional components
function TaskCard(props: TaskCardProps) { ... }

// ❌ Default exports in utils
export default function formatDate() { ... }

// ✅ Named exports
export function formatDate() { ... }

// ❌ Any type
function process(data: any) { ... }

// ✅ Proper types
function process(data: Task[]) { ... }

// ❌ Inline styles
<div style={{ color: 'red', fontSize: '16px' }}>

// ✅ Tailwind classes
<div className="text-red-600 text-base">

// ❌ Mutating state
tasks.push(newTask)
setTasks(tasks)

// ✅ Immutable updates
setTasks([...tasks, newTask])

// ❌ useEffect without dependencies
useEffect(() => {
  fetchData()
})  // Runs on every render!

// ✅ Proper dependencies
useEffect(() => {
  fetchData()
}, [taskId])  // Only when taskId changes
```

---

## ✅ Pre-Commit Checklist

```bash
# 1. Type check
npm run type-check

# 2. Lint
npm run lint

# 3. Format
npm run format  # If using Prettier

# 4. Test
npm test

# 5. Build check
npm run build
```

---

**TypeScript strict mode is not optional. Every 'any' type is a bug.**

