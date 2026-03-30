import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { DragDropContext, Droppable, Draggable, type DropResult } from "@hello-pangea/dnd";
import { getApplications, updateApplication, deleteApplication } from "../api/client";
import { TierBadge } from "../components/ui/TierBadge";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { Trash2 } from "lucide-react";
import type { Application } from "../types";

const COLUMNS = ["saved", "applied", "interview", "offer", "rejected"] as const;
const COLUMN_LABELS: Record<string, string> = {
  saved: "Saved", applied: "Applied", interview: "Interview", offer: "Offer", rejected: "Rejected",
};
const COLUMN_COLORS: Record<string, string> = {
  saved: "border-slate-500", applied: "border-tier-a", interview: "border-violet-500",
  offer: "border-tier-s", rejected: "border-tier-c",
};

export default function Applications() {
  const queryClient = useQueryClient();
  const { data: apps, isLoading } = useQuery({
    queryKey: ["applications"],
    queryFn: () => getApplications(),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => updateApplication(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteApplication(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  const onDragEnd = (result: DropResult) => {
    if (!result.destination) return;
    const newStatus = result.destination.droppableId;
    const appId = parseInt(result.draggableId);
    updateMut.mutate({ id: appId, status: newStatus });
  };

  if (isLoading) return <LoadingSpinner />;

  const grouped: Record<string, Application[]> = {};
  COLUMNS.forEach((c) => (grouped[c] = []));
  apps?.forEach((app) => {
    if (grouped[app.status]) grouped[app.status].push(app);
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Applications</h1>
      {(!apps || apps.length === 0) && (
        <p className="text-slate-400">No applications yet. Save jobs from the Jobs page to get started.</p>
      )}
      <DragDropContext onDragEnd={onDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {COLUMNS.map((status) => (
            <Droppable key={status} droppableId={status}>
              {(provided) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className={`w-64 flex-shrink-0 bg-dark-800 rounded-xl border-t-2 ${COLUMN_COLORS[status]} min-h-[400px] p-3`}
                >
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-sm font-semibold">{COLUMN_LABELS[status]}</h3>
                    <span className="text-xs text-slate-400 bg-dark-700 px-2 py-0.5 rounded">
                      {grouped[status].length}
                    </span>
                  </div>
                  {grouped[status].map((app, index) => (
                    <Draggable key={app.id} draggableId={String(app.id)} index={index}>
                      {(provided) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          className="bg-dark-900 rounded-lg p-3 mb-2 border border-dark-700 hover:border-dark-600"
                        >
                          <div className="flex justify-between items-start mb-1">
                            <TierBadge tier={app.job_tier} />
                            <button
                              onClick={() => deleteMut.mutate(app.id)}
                              className="text-slate-500 hover:text-tier-c"
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                          <p className="text-sm font-medium truncate">{app.job_title}</p>
                          <p className="text-xs text-slate-400 truncate">{app.job_company}</p>
                          {app.job_score && (
                            <p className="text-xs text-slate-500 mt-1">Score: {app.job_score}</p>
                          )}
                          {app.notes && (
                            <p className="text-xs text-slate-500 mt-1 truncate">{app.notes}</p>
                          )}
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          ))}
        </div>
      </DragDropContext>
    </div>
  );
}
