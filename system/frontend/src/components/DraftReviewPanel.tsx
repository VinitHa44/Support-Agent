import React, { useState, useEffect, useRef } from 'react';
import { Edit2, Send, Mail, User, FileText, CheckCircle, RotateCcw, X } from 'lucide-react';

interface DraftData {
  from: string;
  body: string;
  subject: string;
  drafts: string[];
}

interface DraftReviewPanelProps {
  draftData: DraftData;
  onSend: (response: { is_skip: boolean; body: string }) => void;
  queueCount: number;
}

const DraftReviewPanel: React.FC<DraftReviewPanelProps> = ({ draftData, onSend, queueCount }) => {
  const [selectedDraftIndex, setSelectedDraftIndex] = useState(0);
  const [editedDraft, setEditedDraft] = useState(draftData.drafts[0] || '');
  const [isEditing, setIsEditing] = useState(false);
  
  // Create a unique identifier for the current draft data to detect when new data arrives
  const currentDraftId = useRef<string>('');
  
  // Effect to handle new draft data
  useEffect(() => {
    // Create a unique identifier for this draft data
    const newDraftId = `${draftData.from}-${draftData.subject}-${draftData.drafts.join('|')}`;
    
    // Only reset state if we received genuinely new draft data
    if (currentDraftId.current !== newDraftId) {
      console.log('New draft data detected, resetting to draft 1');
      setSelectedDraftIndex(0);
      setEditedDraft(draftData.drafts[0] || '');
      setIsEditing(false);
      currentDraftId.current = newDraftId;
    }
  }, [draftData]);

  const handleDraftSelect = (index: number) => {
    setSelectedDraftIndex(index);
    setEditedDraft(draftData.drafts[index]);
    setIsEditing(false);
  };

  const handleSendDraft = () => {
    if (editedDraft.trim()) {
      onSend({ is_skip: false, body: editedDraft });
    }
  };

  const handleCancelDraft = () => {
    onSend({ is_skip: true, body: "" });
  };

  const InfoCard: React.FC<{ icon: React.ReactNode; title: string; children: React.ReactNode }> = ({ icon, title, children }) => (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center mb-2">
        {icon}
        <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 ml-2">{title}</h3>
      </div>
      <div className="text-sm text-gray-900 dark:text-gray-100">{children}</div>
    </div>
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
      {/* Left Column: Incoming Email */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700 space-y-6">
        <div className="flex items-center">
          <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded-full mr-4">
            <Mail className="h-6 w-6 text-gray-600 dark:text-gray-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-800 dark:text-white">Incoming Email</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">The original email from the customer</p>
          </div>
        </div>
        
        <div className="space-y-4">
          <InfoCard icon={<User size={16} className="text-gray-500 dark:text-gray-400" />} title="From">
            {draftData.from}
          </InfoCard>
          <InfoCard icon={<FileText size={16} className="text-gray-500 dark:text-gray-400" />} title="Subject">
            {draftData.subject}
          </InfoCard>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">Content</h3>
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-md border dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300 max-h-96 overflow-y-auto">
            <pre className="whitespace-pre-wrap font-sans">{draftData.body}</pre>
          </div>
        </div>
      </div>

      {/* Right Column: AI Response */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded-full mr-4">
              <CheckCircle className="h-6 w-6 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-800 dark:text-white">AI Response</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">Review, edit, and send the best response</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {queueCount > 1 && (
              <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full text-xs font-semibold">
                {queueCount - 1} more pending
              </span>
            )}
            <div className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-3 py-1 rounded-full text-xs font-semibold">
              {draftData.drafts.length} DRAFTS
            </div>
          </div>
        </div>

        {/* Draft Tabs */}
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          {draftData.drafts.map((_, index) => (
            <button
              key={index}
              onClick={() => handleDraftSelect(index)}
              className={`px-4 py-2 text-sm font-semibold transition-colors duration-200 ${
                selectedDraftIndex === index
                  ? 'border-b-2 border-gray-800 dark:border-gray-200 text-gray-900 dark:text-white'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Draft {index + 1}
            </button>
          ))}
        </div>

        {/* Draft Content */}
        <div>
          <div className="flex justify-end mb-2">
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="flex items-center px-3 py-1.5 rounded-md text-xs font-semibold transition-colors duration-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300"
            >
              <Edit2 size={12} className="mr-1.5" />
              {isEditing ? 'Preview' : 'Edit'}
            </button>
          </div>
          
          <div className="min-h-[250px]">
            {isEditing ? (
              <textarea
                value={editedDraft}
                onChange={(e) => setEditedDraft(e.target.value)}
                className="w-full h-64 p-4 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:outline-none focus:ring-1 focus:ring-gray-500 dark:focus:ring-gray-400 text-sm leading-relaxed"
                placeholder="Edit your draft..."
              />
            ) : (
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-100 dark:border-gray-600">
                <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
                  {editedDraft}
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                setEditedDraft(draftData.drafts[selectedDraftIndex]);
                setIsEditing(false);
              }}
              className="flex items-center px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
            >
              <RotateCcw size={14} className="mr-2" />
              Reset
            </button>
            
            <button
              onClick={handleCancelDraft}
              className="flex items-center px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-300 bg-red-100 dark:bg-red-900 rounded-lg hover:bg-red-200 dark:hover:bg-red-800 transition-colors duration-200 border border-red-200 dark:border-red-800"
            >
              <X size={14} className="mr-2" />
              Cancel
            </button>
          </div>
          
          <button
            onClick={handleSendDraft}
            disabled={!editedDraft.trim()}
            className="inline-flex items-center px-6 py-2.5 text-sm font-semibold text-white bg-gray-800 dark:bg-gray-200 dark:text-gray-800 rounded-lg hover:bg-gray-900 dark:hover:bg-gray-300 disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors duration-200"
          >
            Send Final Draft
            <Send size={14} className="ml-2" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default DraftReviewPanel; 