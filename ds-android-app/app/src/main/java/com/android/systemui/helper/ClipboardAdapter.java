package com.android.systemui.helper;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.recyclerview.widget.RecyclerView;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class ClipboardAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder> {
    private static final int TYPE_DATE_HEADER = 0;
    private static final int TYPE_CLIPBOARD_ITEM = 1;
    
    private Context context;
    private List<ClipboardManagerActivity.ClipboardItem> items;
    private SimpleDateFormat dateFormat;
    private SimpleDateFormat timeFormat;
    private OnItemClickListener listener;
    
    public interface OnItemClickListener {
        void onItemCopied(ClipboardManagerActivity.ClipboardItem item);
        void onItemLongClick(ClipboardManagerActivity.ClipboardItem item);
    }
    
    public ClipboardAdapter(Context context, List<ClipboardManagerActivity.ClipboardItem> items) {
        this.context = context;
        this.items = items;
        this.dateFormat = new SimpleDateFormat("MMM dd, yyyy", Locale.getDefault());
        this.timeFormat = new SimpleDateFormat("hh:mm:ss a", Locale.getDefault());
    }
    
    public void setOnItemClickListener(OnItemClickListener listener) {
        this.listener = listener;
    }
    
    public void updateData(List<ClipboardManagerActivity.ClipboardItem> newItems) {
        // Create a new list to force update
        this.items = new java.util.ArrayList<>(newItems);
        notifyDataSetChanged();
    }
    
    @Override
    public int getItemViewType(int position) {
        // For simplicity, we'll just show items without date headers for now
        return TYPE_CLIPBOARD_ITEM;
    }
    
    @Override
    public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
            .inflate(R.layout.clipboard_item, parent, false);
        return new ClipboardItemViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(RecyclerView.ViewHolder holder, int position) {
        if (holder instanceof ClipboardItemViewHolder) {
            ClipboardItemViewHolder itemHolder = (ClipboardItemViewHolder) holder;
            ClipboardManagerActivity.ClipboardItem item = items.get(position);
            
            // Truncate content if too long
            String displayContent = item.content;
            if (displayContent.length() > 100) {
                displayContent = displayContent.substring(0, 97) + "...";
            }
            
            itemHolder.contentText.setText(displayContent);
            itemHolder.timeText.setText(timeFormat.format(new Date(item.timestamp)));
            
            // Show date
            itemHolder.dateText.setText(dateFormat.format(new Date(item.timestamp)));
            itemHolder.dateText.setVisibility(View.VISIBLE);
            
            // Show source app if available
            if (item.sourceApp != null && !item.sourceApp.isEmpty()) {
                itemHolder.sourceText.setText(item.sourceApp);
                itemHolder.sourceText.setVisibility(View.VISIBLE);
            } else {
                itemHolder.sourceText.setVisibility(View.GONE);
            }
            
            // Copy button click
            itemHolder.copyButton.setOnClickListener(v -> {
                copyToClipboard(item.content);
                Toast.makeText(context, "Copied to clipboard", Toast.LENGTH_SHORT).show();
                if (listener != null) {
                    listener.onItemCopied(item);
                }
            });
            
            // Long click to show full content
            itemHolder.itemView.setOnLongClickListener(v -> {
                if (listener != null) {
                    listener.onItemLongClick(item);
                }
                return true;
            });
        }
    }
    
    @Override
    public int getItemCount() {
        return items != null ? items.size() : 0;
    }
    
    private void copyToClipboard(String text) {
        ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
        ClipData clip = ClipData.newPlainText("Clipboard Manager", text);
        clipboard.setPrimaryClip(clip);
    }
    
    static class ClipboardItemViewHolder extends RecyclerView.ViewHolder {
        TextView contentText;
        TextView timeText;
        TextView dateText;
        TextView sourceText;
        ImageView copyButton;
        
        ClipboardItemViewHolder(View itemView) {
            super(itemView);
            contentText = itemView.findViewById(R.id.content_text);
            timeText = itemView.findViewById(R.id.time_text);
            dateText = itemView.findViewById(R.id.date_text);
            sourceText = itemView.findViewById(R.id.source_text);
            copyButton = itemView.findViewById(R.id.copy_button);
        }
    }
}