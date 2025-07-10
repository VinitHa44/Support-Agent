import React, { useState } from 'react';
import { Edit2, Send, Mail, User, FileText, CheckCircle, RotateCcw } from 'lucide-react';

interface DraftData {
  from: string;
  body: string;
  subject: string;
  drafts: string[];
}

interface DraftReviewPanelProps {
  draftData: DraftData;
  onSend: (draft: string) => void;
  queueCount: number;
}

const DraftReviewPanel: React.FC<DraftReviewPanelProps> = ({ draftData, onSend, queueCount }) => {
  const [selectedDraftIndex, setSelectedDraftIndex] = useState(0);
  const [editedDraft, setEditedDraft] = useState(draftData.drafts[0] || '');
  const [isEditing, setIsEditing] = useState(false);

  const handleDraftSelect = (index: number) => {
    setSelectedDraftIndex(index);
    setEditedDraft(draftData.drafts[index]);
    setIsEditing(false);
  };

  const handleSendDraft = () => {
    if (editedDraft.trim()) {
      onSend(editedDraft);
    }
  };

  const InfoCard: React.FC<{ icon: React.ReactNode; title: string; children: React.ReactNode }> = ({ icon, title, children }) => (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <div className="flex items-center mb-2">
        {icon}
        <h3 className="text-sm font-semibold text-gray-600 ml-2">{title}</h3>
      </div>
      <div className="text-sm text-gray-900">{children}</div>
    </div>
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
      {/* Left Column: Incoming Email */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-6">
        <div className="flex items-center">
          <div className="bg-gray-100 p-3 rounded-full mr-4">
            <Mail className="h-6 w-6 text-gray-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-800">Incoming Email</h2>
            <p className="text-sm text-gray-500">The original email from the customer</p>
          </div>
        </div>
        
        <div className="space-y-4">
          <InfoCard icon={<User size={16} className="text-gray-500" />} title="From">
            {draftData.from}
          </InfoCard>
          <InfoCard icon={<FileText size={16} className="text-gray-500" />} title="Subject">
            {draftData.subject}
          </InfoCard>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-gray-600 mb-2">Content</h3>
          <div className="bg-gray-50 p-4 rounded-md border text-sm text-gray-700 max-h-96 overflow-y-auto">
            <pre className="whitespace-pre-wrap font-sans">{draftData.body}</pre>
          </div>
        </div>
      </div>

      {/* Right Column: AI Response */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="bg-gray-100 p-3 rounded-full mr-4">
              <CheckCircle className="h-6 w-6 text-gray-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-800">AI Response</h2>
              <p className="text-sm text-gray-500">Review, edit, and send the best response</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {queueCount > 1 && (
              <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-semibold">
                {queueCount - 1} more pending
              </span>
            )}
            <div className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-xs font-semibold">
              {draftData.drafts.length} DRAFTS
            </div>
          </div>
        </div>

        {/* Draft Tabs */}
        <div className="flex border-b border-gray-200">
          {draftData.drafts.map((_, index) => (
            <button
              key={index}
              onClick={() => handleDraftSelect(index)}
              className={`px-4 py-2 text-sm font-semibold transition-colors duration-200 ${
                selectedDraftIndex === index
                  ? 'border-b-2 border-gray-800 text-gray-900'
                  : 'text-gray-500 hover:text-gray-700'
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
              className="flex items-center px-3 py-1.5 rounded-md text-xs font-semibold transition-colors duration-200 bg-gray-100 hover:bg-gray-200 text-gray-700"
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
                className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-gray-500 text-sm leading-relaxed"
                placeholder="Edit your draft..."
              />
            ) : (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800 leading-relaxed">
                  {editedDraft}
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <button
            onClick={() => {
              setEditedDraft(draftData.drafts[selectedDraftIndex]);
              setIsEditing(false);
            }}
            className="flex items-center px-4 py-2 text-sm font-semibold text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors duration-200"
          >
            <RotateCcw size={14} className="mr-2" />
            Reset
          </button>
          
          <button
            onClick={handleSendDraft}
            disabled={!editedDraft.trim()}
            className="inline-flex items-center px-6 py-2.5 text-sm font-semibold text-white bg-gray-800 rounded-lg hover:bg-gray-900 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200"
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