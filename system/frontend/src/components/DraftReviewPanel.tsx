import React, { useState } from 'react';
import { Edit2, Send, Mail, User, Calendar, FileText, CheckCircle, Clock } from 'lucide-react';

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
    <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
      {/* Email Details Header */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-b border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <div className="bg-blue-100 p-3 rounded-full mr-4">
              <Mail className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">📧 Email Review</h2>
              <p className="text-gray-600">Customer email requiring response</p>
            </div>
          </div>
          <div className="flex items-center bg-white rounded-lg px-4 py-2 shadow-sm">
            <Clock className="h-4 w-4 text-gray-400 mr-2" />
            <span className="text-sm text-gray-600">{formatDate(new Date().toISOString())}</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="flex items-center mb-2">
              <User className="h-5 w-5 text-blue-600 mr-2" />
              <p className="text-sm font-semibold text-gray-700">From:</p>
            </div>
            <p className="text-gray-900 font-medium">{draftData.from}</p>
          </div>
          
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="flex items-center mb-2">
              <FileText className="h-5 w-5 text-purple-600 mr-2" />
              <p className="text-sm font-semibold text-gray-700">Subject:</p>
            </div>
            <p className="text-gray-900 font-medium">{draftData.subject}</p>
          </div>
        </div>
        
        <div className="mt-6 bg-white rounded-xl p-4 shadow-sm">
          <div className="flex items-center mb-3">
            <Mail className="h-5 w-5 text-green-600 mr-2" />
            <p className="text-sm font-semibold text-gray-700">Original Email:</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border-2 border-gray-100 text-sm text-gray-800 max-h-40 overflow-y-auto">
            <div className="whitespace-pre-wrap">{draftData.body}</div>
          </div>
        </div>
      </div>

      {/* Draft Selection */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <div className="bg-green-100 p-3 rounded-full mr-4">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">🤖 AI Generated Drafts</h3>
              <p className="text-gray-600">Review and select the best response</p>
            </div>
          </div>
          <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-bold">
            {draftData.drafts.length} drafts available
          </div>
        </div>

        {/* Draft Tabs */}
        <div className="flex flex-wrap gap-3 mb-6">
          {draftData.drafts.map((_, index) => (
            <button
              key={index}
              onClick={() => handleDraftSelect(index)}
              className={`px-6 py-3 rounded-xl text-sm font-bold transition-all duration-200 ${
                selectedDraftIndex === index
                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg transform scale-105'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-md'
              }`}
            >
              Draft {index + 1}
            </button>
          ))}
        </div>

        {/* Draft Content */}
        <div className="border-2 border-gray-200 rounded-2xl overflow-hidden shadow-sm">
          <div className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200">
            <h4 className="font-bold text-gray-900 text-lg">
              📝 Draft {selectedDraftIndex + 1}
            </h4>
            <button
              onClick={() => setIsEditing(!isEditing)}
              className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-bold transition-all duration-200 ${
                isEditing
                  ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-md hover:shadow-lg'
                  : 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-md hover:shadow-lg'
              }`}
            >
              <Edit2 className="h-4 w-4 mr-2" />
              {isEditing ? '👁️ Preview' : '✏️ Edit'}
            </button>
          </div>
          
          <div className="p-6">
            {isEditing ? (
              <div className="space-y-4">
                <div className="text-sm text-gray-600 bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                  💡 <strong>Tip:</strong> Edit the draft to better match your tone and add any missing details
                </div>
                <textarea
                  value={editedDraft}
                  onChange={(e) => setEditedDraft(e.target.value)}
                  className="w-full h-48 p-4 border-2 border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-800 leading-relaxed"
                  placeholder="Edit your draft here..."
                />
                <div className="text-xs text-gray-500 text-right">
                  {editedDraft.length} characters
                </div>
              </div>
            ) : (
              <div className="bg-blue-50 rounded-xl p-6 border-2 border-blue-100">
                <div className="whitespace-pre-wrap text-gray-800 leading-relaxed min-h-[200px]">
                  {editedDraft}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between mt-8">
          <button
            onClick={() => {
              setEditedDraft(draftData.drafts[selectedDraftIndex]);
              setIsEditing(false);
            }}
            className="px-6 py-3 text-sm font-bold text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200 transition-all duration-200 shadow-md hover:shadow-lg"
          >
            🔄 Reset Draft
          </button>
          
          <button
            onClick={handleSendDraft}
            disabled={!editedDraft.trim()}
            className="inline-flex items-center px-8 py-4 text-sm font-bold text-white bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl hover:from-green-600 hover:to-emerald-600 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            <Send className="h-5 w-5 mr-2" />
            🚀 Send Final Draft
          </button>
        </div>
      </div>
    </div>
  );
};

export default DraftReviewPanel; 