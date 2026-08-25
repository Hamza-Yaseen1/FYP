# Implementation Plan: Better Inbox

**Branch**: `011-better-inbox` | **Date**: 2026-08-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-better-inbox/spec.md`

## Summary

Improve the existing Inbox page with priority tabs, source/priority/date/sender filters, search functionality, combined filtering, and proper loading/empty/error states. All filtering and search will be handled on the backend to maintain user isolation and performance.

**Primary Requirement**: Users can quickly find and organize communications using tabs, filters, and search.

**Technical Approach**: Extend existing FastAPI backend with query parameters for filtering/search, add MongoDB text indexes, rebuild inbox page using existing components with new filter/search UI.

## Technical Context

**Language/Version**: TypeScript 5.0 (frontend), Python 3.11+ (backend)  
**Primary Dependencies**: Next.js 16.3, FastAPI, MongoDB (Motor async driver), Tailwind CSS, shadcn/ui  
**Storage**: MongoDB (existing `messages` collection)  
**Testing**: Vitest (frontend), pytest (backend)  
**Target Platform**: Web application (desktop + mobile)  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: Filtering/search < 2 seconds, tab switching < 1 second  
**Constraints**: Maintain user isolation, reuse existing components, no new dependencies  
**Scale/Scope**: Single user FYP project, ~100-1000 messages expected

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Simplicity First**: Extending existing components and APIs, not rebuilding from scratch  
✅ **Vertical Slices**: Complete inbox feature with tabs, filters, search, states  
✅ **AI is Assistive**: Not applicable (no new AI features)  
✅ **User Control**: Users can filter, search, and clear filters  
✅ **Security and Privacy**: User isolation maintained at query level  
✅ **Clean Code**: Following existing patterns and conventions  
✅ **Progressive Enhancement**: Loading states, empty states, error states  

**All gates pass. No violations identified.**

## Project Structure

### Documentation (this feature)

```text
specs/011-better-inbox/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── messages-api.md  # API contract for messages endpoints
└── tasks.md             # Phase 2 output (NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Web application structure (existing)
backend/
├── src/
│   ├── models/
│   │   └── message.py      # Message models (existing)
│   ├── routes/
│   │   └── messages.py     # Message API routes (extend)
│   ├── services/
│   │   └── ai/             # AI analysis services (existing)
│   └── tests/
│       └── test_messages.py # Message API tests (extend)

frontend/
├── app/
│   └── (dashboard)/
│       └── inbox/
│           └── page.tsx    # Inbox page (rebuild)
├── components/
│   ├── MessageList.tsx     # Message list component (reuse)
│   ├── MessageCard.tsx     # Message card component (reuse)
│   ├── InboxTabs.tsx       # Priority tabs (new)
│   ├── FilterBar.tsx       # Filter controls (new)
│   ├── SearchBar.tsx       # Search input (new)
│   └── EmptyState.tsx      # Empty state component (new)
└── lib/
    └── api.ts              # API client (existing)
```

**Structure Decision**: Extend existing web application structure. No new directories required.

## Implementation Steps

### Phase 1: Backend API Extensions

**Goal**: Add filtering and search capabilities to existing message API

#### Step 1.1: Add MongoDB Text Index

**File**: `backend/main.py`

**Changes**:
- Add text index on `sender`, `content`, `ai_analysis.summary` fields
- This enables efficient text search across multiple fields

**Implementation**:
```python
# In startup event or initialization
await messages_collection.create_index([
    ("sender", "text"),
    ("content", "text"),
    ("ai_analysis.summary", "text")
])
```

#### Step 1.2: Extend GET /messages Endpoint

**File**: `backend/routes/messages.py`

**Changes**:
- Add query parameters: `tab`, `source`, `priority`, `start_date`, `end_date`, `sender`, `search`, `limit`, `offset`
- Build dynamic MongoDB query based on parameters
- Maintain user isolation (`user_id` filter always included)
- Return paginated results with total count

**Implementation**:
```python
@router.get("/messages")
async def get_messages(
    current_user: dict = Depends(get_current_user),
    tab: str = Query("all", description="Priority tab filter"),
    source: Optional[str] = Query(None, description="Source filter"),
    priority: Optional[str] = Query(None, description="Priority filter"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    sender: Optional[str] = Query(None, description="Sender filter"),
    search: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    uid = str(current_user["_id"])
    query = {"user_id": uid}
    
    # Tab filter
    if tab == "urgent":
        query["ai_analysis.priority"] = "urgent"
    elif tab == "important":
        query["ai_analysis.priority"] = "important"
    elif tab == "normal":
        query["ai_analysis.priority"] = "normal"
    elif tab == "unread":
        query["status"] = "unread"
    
    # Additional filters
    if source:
        query["source"] = source
    if priority:
        query["ai_analysis.priority"] = priority
    if sender:
        query["sender"] = sender
    if start_date or end_date:
        query["created_at"] = {}
        if start_date:
            query["created_at"]["$gte"] = start_date
        if end_date:
            query["created_at"]["$lte"] = end_date
    if search:
        query["$text"] = {"$search": search}
    
    # Execute query
    total = await messages_collection.count_documents(query)
    messages = await messages_collection.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    
    return {"messages": messages, "total": total, "limit": limit, "offset": offset}
```

#### Step 1.3: Add GET /messages/counts Endpoint

**File**: `backend/routes/messages.py`

**Changes**:
- New endpoint to get filter counts
- Use MongoDB aggregation pipeline
- Return counts for tabs, sources, priorities, senders

**Implementation**:
```python
@router.get("/messages/counts")
async def get_message_counts(current_user: dict = Depends(get_current_user)):
    uid = str(current_user["_id"])
    query = {"user_id": uid}
    
    # Aggregation pipeline for counts
    pipeline = [
        {"$match": query},
        {"$facet": {
            "tabs": [
                {"$group": {"_id": "$ai_analysis.priority", "count": {"$sum": 1}}},
                {"$group": {"_id": None, "urgent": {"$sum": {"$cond": [{"$eq": ["$_id", "urgent"]}, "$count", 0]}}, ...}}
            ],
            "sources": [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                {"$push": {"k": "$_id", "v": "$count"}}
            ],
            "priorities": [...],
            "senders": [...]
        }}
    ]
    
    result = await messages_collection.aggregate(pipeline).to_list(1)
    return result[0]
```

#### Step 1.4: Add GET /messages/senders Endpoint

**File**: `backend/routes/messages.py`

**Changes**:
- New endpoint to get unique senders for filter dropdown
- Extract from user's messages only

**Implementation**:
```python
@router.get("/messages/senders")
async def get_message_senders(
    current_user: dict = Depends(get_current_user),
    search: Optional[str] = Query(None)
):
    uid = str(current_user["_id"])
    query = {"user_id": uid}
    
    if search:
        query["sender"] = {"$regex": search, "$options": "i"}
    
    senders = await messages_collection.distinct("sender", query)
    return {"senders": sorted(senders)}
```

#### Step 1.5: Add GET /messages/sources Endpoint

**File**: `backend/routes/messages.py`

**Changes**:
- New endpoint to get unique sources for filter dropdown
- Extract from user's messages only

**Implementation**:
```python
@router.get("/messages/sources")
async def get_message_sources(current_user: dict = Depends(get_current_user)):
    uid = str(current_user["_id"])
    query = {"user_id": uid}
    
    sources = await messages_collection.distinct("source", query)
    return {"sources": sorted(sources)}
```

### Phase 2: Frontend Components

**Goal**: Rebuild inbox page with tabs, filters, search, and states

#### Step 2.1: Create InboxTabs Component

**File**: `components/InboxTabs.tsx` (new)

**Changes**:
- Tab component for All, Urgent, Important, Normal, Unread
- Show count badge for each tab
- Highlight active tab
- Handle tab click

**Implementation**:
```typescript
interface InboxTabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  counts: {
    all: number;
    urgent: number;
    important: number;
    normal: number;
    unread: number;
  };
}

export function InboxTabs({ activeTab, onTabChange, counts }: InboxTabsProps) {
  const tabs = [
    { id: 'all', label: 'All', count: counts.all },
    { id: 'urgent', label: 'Urgent', count: counts.urgent },
    { id: 'important', label: 'Important', count: counts.important },
    { id: 'normal', label: 'Normal', count: counts.normal },
    { id: 'unread', label: 'Unread', count: counts.unread },
  ];
  
  return (
    <div className="flex space-x-2">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`px-4 py-2 rounded-lg ${
            activeTab === tab.id
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {tab.label}
          {tab.count > 0 && (
            <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-gray-200">
              {tab.count}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
```

#### Step 2.2: Create FilterBar Component

**File**: `components/FilterBar.tsx` (new)

**Changes**:
- Dropdown filters for Source, Priority, Sender
- Date range picker
- Clear all button
- Show active filters

**Implementation**:
```typescript
interface FilterBarProps {
  filters: {
    source: string | null;
    priority: string | null;
    sender: string | null;
    startDate: Date | null;
    endDate: Date | null;
  };
  onFilterChange: (filters: FilterBarProps['filters']) => void;
  onClearAll: () => void;
  sources: string[];
  priorities: string[];
  senders: string[];
}

export function FilterBar({ filters, onFilterChange, onClearAll, sources, priorities, senders }: FilterBarProps) {
  // Filter dropdowns implementation
}
```

#### Step 2.3: Create SearchBar Component

**File**: `components/SearchBar.tsx` (new)

**Changes**:
- Search input with placeholder "Search communications..."
- Debounced search (300ms delay)
- Clear button
- Loading indicator

**Implementation**:
```typescript
interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onClear: () => void;
  isLoading: boolean;
}

export function SearchBar({ value, onChange, onClear, isLoading }: SearchBarProps) {
  return (
    <div className="relative">
      <input
        type="text"
        placeholder="Search communications..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-2 pl-10 border rounded-lg"
      />
      {isLoading && (
        <div className="absolute right-3 top-2">
          <LoadingSpinner />
        </div>
      )}
      {value && (
        <button
          onClick={onClear}
          className="absolute right-3 top-2 text-gray-400 hover:text-gray-600"
        >
          ×
        </button>
      )}
    </div>
  );
}
```

#### Step 2.4: Create EmptyState Component

**File**: `components/EmptyState.tsx` (new)

**Changes**:
- Display when no messages match filters
- Show "No communications found" message
- Optional: Show suggestions to clear filters

**Implementation**:
```typescript
interface EmptyStateProps {
  message: string;
  onClearFilters?: () => void;
}

export function EmptyState({ message, onClearFilters }: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      <p className="text-gray-500">{message}</p>
      {onClearFilters && (
        <button
          onClick={onClearFilters}
          className="mt-4 text-blue-600 hover:underline"
        >
          Clear all filters
        </button>
      )}
    </div>
  );
}
```

#### Step 2.5: Rebuild Inbox Page

**File**: `app/(dashboard)/inbox/page.tsx`

**Changes**:
- Replace stub with full implementation
- Add state management for filters, search, loading, error
- Fetch messages with filters from backend
- Render InboxTabs, FilterBar, SearchBar, MessageList
- Handle loading, empty, error states

**Implementation**:
```typescript
'use client';

import { useState, useEffect } from 'react';
import { InboxTabs } from '@/components/InboxTabs';
import { FilterBar } from '@/components/FilterBar';
import { SearchBar } from '@/components/SearchBar';
import { MessageList } from '@/components/MessageList';
import { EmptyState } from '@/components/EmptyState';
import { apiFetch } from '@/lib/api';

export default function InboxPage() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    tab: 'all',
    source: null,
    priority: null,
    sender: null,
    startDate: null,
    endDate: null,
  });
  const [search, setSearch] = useState('');
  const [counts, setCounts] = useState({
    all: 0,
    urgent: 0,
    important: 0,
    normal: 0,
    unread: 0,
  });
  const [sources, setSources] = useState([]);
  const [senders, setSenders] = useState([]);

  // Fetch messages with filters
  useEffect(() => {
    fetchMessages();
  }, [filters, search]);

  // Fetch counts on mount
  useEffect(() => {
    fetchCounts();
    fetchSources();
    fetchSenders();
  }, []);

  const fetchMessages = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filters.tab !== 'all') params.append('tab', filters.tab);
      if (filters.source) params.append('source', filters.source);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.sender) params.append('sender', filters.sender);
      if (filters.startDate) params.append('start_date', filters.startDate.toISOString());
      if (filters.endDate) params.append('end_date', filters.endDate.toISOString());
      if (search) params.append('search', search);
      
      const data = await apiFetch(`/messages?${params.toString()}`);
      setMessages(data.messages);
    } catch (err) {
      setError('Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  const fetchCounts = async () => {
    const data = await apiFetch('/messages/counts');
    setCounts(data.tabs);
  };

  const fetchSources = async () => {
    const data = await apiFetch('/messages/sources');
    setSources(data.sources);
  };

  const fetchSenders = async () => {
    const data = await apiFetch('/messages/senders');
    setSenders(data.senders);
  };

  const handleClearAll = () => {
    setFilters({
      tab: 'all',
      source: null,
      priority: null,
      sender: null,
      startDate: null,
      endDate: null,
    });
    setSearch('');
  };

  if (error) {
    return <div className="text-center py-12 text-red-600">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Inbox</h1>
      
      <InboxTabs
        activeTab={filters.tab}
        onTabChange={(tab) => setFilters({ ...filters, tab })}
        counts={counts}
      />
      
      <FilterBar
        filters={filters}
        onFilterChange={setFilters}
        onClearAll={handleClearAll}
        sources={sources}
        priorities={['urgent', 'important', 'normal']}
        senders={senders}
      />
      
      <SearchBar
        value={search}
        onChange={setSearch}
        onClear={() => setSearch('')}
        isLoading={loading}
      />
      
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : messages.length === 0 ? (
        <EmptyState
          message="No communications found"
          onClearFilters={handleClearAll}
        />
      ) : (
        <MessageList messages={messages} />
      )}
    </div>
  );
}
```

### Phase 3: Testing

**Goal**: Ensure all functionality works correctly and user isolation is maintained

#### Step 3.1: Backend API Tests

**File**: `backend/tests/test_messages.py`

**Tests**:
- Test GET /messages with each filter parameter
- Test GET /messages with combined filters
- Test GET /messages/counts returns correct counts
- Test GET /messages/senders returns unique senders
- Test GET /messages/sources returns unique sources
- Test user isolation: User A cannot see User B's messages
- Test search functionality
- Test date range filtering
- Test pagination

#### Step 3.2: Frontend Component Tests

**Files**: 
- `components/__tests__/InboxTabs.test.tsx`
- `components/__tests__/FilterBar.test.tsx`
- `components/__tests__/SearchBar.test.tsx`
- `components/__tests__/EmptyState.test.tsx`

**Tests**:
- Test tab switching
- Test filter selection
- Test search input
- Test clear all filters
- Test loading states
- Test empty states

#### Step 3.3: Integration Tests

**File**: `app/(dashboard)/inbox/__tests__/page.test.tsx`

**Tests**:
- Test inbox page renders correctly
- Test messages load on mount
- Test filters update message list
- Test search updates message list
- Test error states display
- Test empty states display

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | No violations identified | N/A |

## Next Steps

1. **Phase 0**: Complete research (DONE)
2. **Phase 1**: Implement backend API extensions
3. **Phase 1**: Implement frontend components
4. **Phase 2**: Write tests
5. **Phase 2**: Manual testing
6. **Phase 2**: Performance optimization
7. **Phase 2**: Documentation updates