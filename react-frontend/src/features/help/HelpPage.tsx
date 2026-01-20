/**
 * Help Page
 * 
 * Provides documentation, FAQ, and video tutorials for PEARL users.
 * Includes searchable FAQ with collapsible sections.
 */

import { useState, useMemo } from 'react';
import { 
  Search, 
  BookOpen, 
  PlayCircle, 
  MessageCircle, 
  ChevronDown, 
  ChevronRight,
  FileText,
  Users,
  Package,
  BarChart3,
  Settings,
  Shield,
  ExternalLink,
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

// FAQ Categories and Questions
const FAQ_DATA = [
  {
    category: 'Getting Started',
    icon: BookOpen,
    questions: [
      {
        q: 'How do I create my first study?',
        a: 'Navigate to Studies in the sidebar, click "Add Study", enter a study label (e.g., "STUDY-001"), and click Create. Your study will appear in the list immediately.',
      },
      {
        q: 'What is a Database Release?',
        a: 'A Database Release represents a snapshot of your clinical trial data at a specific point in time. Each study can have multiple releases (e.g., interim, final). Create releases under each study to organize your reporting efforts.',
      },
      {
        q: 'How do I add team members?',
        a: 'Go to User Management (admin only), click "Add User", enter their details and assign a role. Users will receive an email to set their password. You can also assign users to specific studies with different roles.',
      },
    ],
  },
  {
    category: 'Packages & TFL Management',
    icon: Package,
    questions: [
      {
        q: 'What is the difference between a Package and a TFL?',
        a: 'A Package is a collection of related outputs (Tables, Figures, Listings) and Datasets. TFLs are individual items within a package. For example, "Safety Package" might contain "AE Summary Table", "AE Listing", and the ADAE dataset.',
      },
      {
        q: 'How do I create a TFL Package?',
        a: 'Go to Packages, click "Add Package", give it a name (e.g., "PKG-SAFETY"). Then add items to the package specifying the type (TLF or Dataset), subtype (Table/Listing/Figure or SDTM/ADaM), and item code.',
      },
      {
        q: 'What are Text Elements?',
        a: 'Text Elements are reusable text snippets for your TFLs: Titles, Footnotes, Population definitions (like SAFFL, ITTFL), Acronyms (like AE, SAE), and ICH Categories. Define them once and reuse across multiple outputs.',
      },
    ],
  },
  {
    category: 'Tracker & Workflow',
    icon: BarChart3,
    questions: [
      {
        q: 'How does the tracker workflow work?',
        a: 'Each TFL item goes through a workflow: Not Started → In Progress → Ready for QC → QC In Progress → Completed. Assign a Production Programmer and QC Programmer to each item. The tracker shows real-time status across your team.',
      },
      {
        q: 'Can I assign the same person as Production and QC?',
        a: 'No, for quality assurance purposes, the Production Programmer and QC Programmer must be different people. This ensures independent review of all outputs.',
      },
      {
        q: 'What happens when I mark QC as completed?',
        a: 'When QC is marked as completed, the Production status is automatically set to completed as well. This indicates the item has passed quality review and is ready for delivery.',
      },
      {
        q: 'How do comments work on trackers?',
        a: 'Each tracker item has a comment thread. Team members can add comments, mention other users with @username, and mark comments as resolved. Unresolved comments prevent marking QC as completed.',
      },
    ],
  },
  {
    category: 'User Roles & Permissions',
    icon: Shield,
    questions: [
      {
        q: 'What are the different user roles?',
        a: 'Admin: Full system access including user management. LEAD: Can manage assigned studies, releases, packages. EDITOR: Can edit tracker data in assigned studies. VIEWER: Read-only access to assigned studies.',
      },
      {
        q: 'How do I assign users to studies?',
        a: 'As an admin or study LEAD, go to the study details and click "Manage Members". You can add users and assign them roles (LEAD, EDITOR, or VIEWER) for that specific study.',
      },
      {
        q: 'Can a user have different roles in different studies?',
        a: 'Yes! A user might be a LEAD for Study A but only an EDITOR for Study B. Role assignments are per-study, giving you flexibility in team organization.',
      },
    ],
  },
  {
    category: 'Account & Settings',
    icon: Settings,
    questions: [
      {
        q: 'How do I change my password?',
        a: 'Click your username in the top-right corner, then select "Settings" or "Profile". You can change your password from there. You can also use "Forgot Password" on the login page.',
      },
      {
        q: 'How do I manage my subscription?',
        a: 'Admins can access billing settings from Settings → Billing. You can view your current plan, upgrade/downgrade, update payment methods, and access invoices through the Stripe billing portal.',
      },
      {
        q: 'How do I reset the demo data?',
        a: 'Admins can reset to sample data from Settings → Data Management. This will clear all existing data and restore the demo studies, packages, and text elements. Use with caution!',
      },
    ],
  },
];

// Video Tutorials
const VIDEO_TUTORIALS = [
  {
    title: 'Getting Started with PEARL',
    description: 'Learn the basics: creating studies, releases, and your first reporting effort.',
    duration: '5:30',
    thumbnail: '/thumbnails/getting-started.jpg',
    url: '#', // Placeholder - would link to actual video
  },
  {
    title: 'Managing TFL Packages',
    description: 'How to create packages, add items, and organize your deliverables.',
    duration: '4:15',
    thumbnail: '/thumbnails/packages.jpg',
    url: '#',
  },
  {
    title: 'Using the Tracker',
    description: 'Track production and QC status, assign programmers, and monitor progress.',
    duration: '6:45',
    thumbnail: '/thumbnails/tracker.jpg',
    url: '#',
  },
  {
    title: 'Team Management',
    description: 'Add users, assign roles, and manage study-level permissions.',
    duration: '3:20',
    thumbnail: '/thumbnails/team.jpg',
    url: '#',
  },
];

export function HelpPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [openCategories, setOpenCategories] = useState<string[]>([FAQ_DATA[0].category]);

  // Filter FAQs based on search
  const filteredFAQ = useMemo(() => {
    if (!searchQuery.trim()) return FAQ_DATA;
    
    const query = searchQuery.toLowerCase();
    return FAQ_DATA.map(category => ({
      ...category,
      questions: category.questions.filter(
        q => q.q.toLowerCase().includes(query) || q.a.toLowerCase().includes(query)
      ),
    })).filter(category => category.questions.length > 0);
  }, [searchQuery]);

  const toggleCategory = (category: string) => {
    setOpenCategories(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  return (
    <div className="container mx-auto py-6 px-4 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Help Center</h1>
        <p className="text-gray-600">
          Find answers, watch tutorials, and get the most out of PEARL.
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-8">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <Input
          type="text"
          placeholder="Search for help..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10 py-6 text-lg"
        />
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card className="hover:border-indigo-500 cursor-pointer transition-colors">
          <CardContent className="p-4 flex flex-col items-center text-center">
            <BookOpen className="h-8 w-8 text-indigo-500 mb-2" />
            <span className="font-medium">Documentation</span>
          </CardContent>
        </Card>
        <Card className="hover:border-indigo-500 cursor-pointer transition-colors">
          <CardContent className="p-4 flex flex-col items-center text-center">
            <PlayCircle className="h-8 w-8 text-indigo-500 mb-2" />
            <span className="font-medium">Video Tutorials</span>
          </CardContent>
        </Card>
        <Card className="hover:border-indigo-500 cursor-pointer transition-colors">
          <CardContent className="p-4 flex flex-col items-center text-center">
            <MessageCircle className="h-8 w-8 text-indigo-500 mb-2" />
            <span className="font-medium">Contact Support</span>
          </CardContent>
        </Card>
        <Card className="hover:border-indigo-500 cursor-pointer transition-colors">
          <CardContent className="p-4 flex flex-col items-center text-center">
            <FileText className="h-8 w-8 text-indigo-500 mb-2" />
            <span className="font-medium">Release Notes</span>
          </CardContent>
        </Card>
      </div>

      {/* Video Tutorials Section */}
      <section className="mb-10">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <PlayCircle className="h-5 w-5 text-indigo-500" />
          Video Tutorials
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {VIDEO_TUTORIALS.map((video, index) => (
            <Card key={index} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="p-4">
                <div className="flex gap-4">
                  <div className="w-24 h-16 bg-gray-200 rounded flex items-center justify-center flex-shrink-0">
                    <PlayCircle className="h-8 w-8 text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 truncate">{video.title}</h3>
                    <p className="text-sm text-gray-500 line-clamp-2">{video.description}</p>
                    <span className="text-xs text-gray-400 mt-1 block">{video.duration}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* FAQ Section */}
      <section>
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <MessageCircle className="h-5 w-5 text-indigo-500" />
          Frequently Asked Questions
        </h2>

        {filteredFAQ.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-gray-500">
              No results found for "{searchQuery}". Try a different search term.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredFAQ.map((category) => {
              const Icon = category.icon;
              const isOpen = openCategories.includes(category.category);
              
              return (
                <Card key={category.category}>
                  <Collapsible open={isOpen} onOpenChange={() => toggleCategory(category.category)}>
                    <CollapsibleTrigger asChild>
                      <CardHeader className="cursor-pointer hover:bg-gray-50 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Icon className="h-5 w-5 text-indigo-500" />
                            <CardTitle className="text-lg">{category.category}</CardTitle>
                            <span className="text-sm text-gray-400">
                              ({category.questions.length} questions)
                            </span>
                          </div>
                          {isOpen ? (
                            <ChevronDown className="h-5 w-5 text-gray-400" />
                          ) : (
                            <ChevronRight className="h-5 w-5 text-gray-400" />
                          )}
                        </div>
                      </CardHeader>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <CardContent className="pt-0">
                        <div className="space-y-4">
                          {category.questions.map((faq, index) => (
                            <div key={index} className="border-b last:border-0 pb-4 last:pb-0">
                              <h4 className="font-medium text-gray-900 mb-2">{faq.q}</h4>
                              <p className="text-gray-600 text-sm">{faq.a}</p>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </CollapsibleContent>
                  </Collapsible>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      {/* Contact Support */}
      <section className="mt-10">
        <Card className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
          <CardContent className="p-6 flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-xl font-semibold mb-1">Still need help?</h3>
              <p className="text-indigo-100">
                Our support team is here to assist you with any questions.
              </p>
            </div>
            <Button variant="secondary" className="whitespace-nowrap">
              <MessageCircle className="h-4 w-4 mr-2" />
              Contact Support
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
