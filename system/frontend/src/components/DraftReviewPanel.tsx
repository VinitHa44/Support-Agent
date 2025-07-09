import React, { useState } from 'react';
import { Edit2, Send, Mail, User, Calendar } from 'lucide-react';

interface DraftData {
  from: string;
  body: string;
  subject: string;
  drafts: string[];
}

interface DraftReviewPanelProps {
  draftData: DraftData;
  onSendDraft: (draft: string) => void;
}

const DraftReviewPanel: React.FC<DraftReviewPanelProps> = ({ draftData, onSendDraft }) => {
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
      onSendDraft(editedDraft);
    }
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleString();
  };

  return (
    <div className="bg-white shadow-sm rounded-lg overflow-hidden">
      {/* Email Details Header */}
      <div className="border-b border-gray-200 bg-gray-50 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Email Details</h2>
          <div className="flex items-center text-sm text-gray-500">
            <Calendar className="h-4 w-4 mr-1" />
            {formatDate(new Date().toISOString())}
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center">
            <User className="h-5 w-5 text-gray-400 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-700">From:</p>
              <p className="text-sm text-gray-900">{draftData.from}</p>
            </div>
          </div>
          
          <div className="flex items-center">
            <Mail className="h-5 w-5 text-gray-400 mr-2" />
            <div>
              <p className="text-sm font-medium text-gray-700">Subject:</p>
              <p className="text-sm text-gray-900">{draftData.subject}</p>
            </div>
          </div>
        </div>
        
        <div className="mt-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Original Email:</p>
          <div className="bg-white p-3 rounded border text-sm text-gray-800 max-h-32 overflow-y-auto">
            {draftData.body}
          </div>
        </div>
      </div>

      {/* Draft Selection */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Generated Drafts</h3>
          <div className="flex items-center text-sm text-gray-500">
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
              {draftData.drafts.length} drafts available
            </span>
          </div>
        </div>

        {/* Draft Tabs */}
        <div className="flex space-x-2 mb-4">
          {draftData.drafts.map((_, index) => (
            <button
              key={index}
              onClick={() => handleDraftSelect(index)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedDraftIndex === index
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Draft {index + 1}
            </button>
          ))}
        </div>

        {/* Draft Content */}
        <div className="border border-gray-200 rounded-lg">
          <div className="flex items-center justify-between p-3 bg-gray-50 border-b">
            <h4 className="font-medium text-gray-900">
              Draft {selectedDraftIndex + 1}
            </h4>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className={`inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                isEditing
                  ? 'bg-green-100 text-green-800 hover:bg-green-200'
                  : 'bg-blue-100 text-blue-800 hover:bg-blue-200'
              }`}
            >
              <Edit2 className="h-4 w-4 mr-1" />
              {isEditing ? 'Preview' : 'Edit'}
            </button>
          </div>
          
          <div className="p-4">
            {isEditing ? (
              <textarea
                value={editedDraft}
                onChange={(e) => setEditedDraft(e.target.value)}
                className="w-full h-40 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder="Edit your draft here..."
              />
            ) : (
              <div className="prose max-w-none">
                <div className="whitespace-pre-wrap text-gray-800 bg-gray-50 p-3 rounded border min-h-[160px]">
                  {editedDraft}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-3 mt-6">
          <button
            onClick={() => {
              setEditedDraft(draftData.drafts[selectedDraftIndex]);
              setIsEditing(false);
            }}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Reset
          </button>
          
          <button
            onClick={handleSendDraft}
            disabled={!editedDraft.trim()}
            className="inline-flex items-center px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-4 w-4 mr-2" />
            Send Final Draft
          </button>
        </div>
      </div>
    </div>
  );
};

export default DraftReviewPanel; 