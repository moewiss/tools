#!/usr/bin/env python3
"""
Download History Manager
Tracks all downloads, provides history, queue management, and re-download functionality
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from threading import Lock

class DownloadHistory:
    def __init__(self, db_path='download_history.db'):
        self.db_path = db_path
        self.lock = Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Downloads history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    format_type TEXT,
                    quality TEXT,
                    file_size INTEGER,
                    file_path TEXT,
                    thumbnail_url TEXT,
                    duration INTEGER,
                    status TEXT DEFAULT 'pending',
                    downloaded_date TIMESTAMP,
                    error_message TEXT,
                    job_id TEXT,
                    is_playlist BOOLEAN DEFAULT 0,
                    playlist_title TEXT,
                    video_count INTEGER
                )
            ''')
            
            # Download queue table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    download_id INTEGER,
                    priority INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'queued',
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_date TIMESTAMP,
                    completed_date TIMESTAMP,
                    FOREIGN KEY (download_id) REFERENCES downloads(id)
                )
            ''')
            
            conn.commit()
    
    def add_download(self, url, title=None, format_type='video', quality='best', 
                     job_id=None, is_playlist=False, playlist_title=None, video_count=None):
        """Add a new download to history"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO downloads 
                    (url, title, format_type, quality, status, downloaded_date, job_id, 
                     is_playlist, playlist_title, video_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (url, title, format_type, quality, 'in_progress', 
                      datetime.now().isoformat(), job_id, is_playlist, 
                      playlist_title, video_count))
                
                download_id = cursor.lastrowid
                conn.commit()
                
                return download_id
    
    def update_download(self, download_id, **kwargs):
        """Update download information"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build UPDATE query dynamically
                fields = []
                values = []
                
                for key, value in kwargs.items():
                    fields.append(f"{key} = ?")
                    values.append(value)
                
                if fields:
                    query = f"UPDATE downloads SET {', '.join(fields)} WHERE id = ?"
                    values.append(download_id)
                    cursor.execute(query, values)
                    conn.commit()
    
    def get_download(self, download_id):
        """Get a single download by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM downloads WHERE id = ?', (download_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def get_all_downloads(self, limit=100, status=None):
        """Get all downloads, optionally filtered by status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM downloads 
                    WHERE status = ? 
                    ORDER BY downloaded_date DESC 
                    LIMIT ?
                ''', (status, limit))
            else:
                cursor.execute('''
                    SELECT * FROM downloads 
                    ORDER BY downloaded_date DESC 
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def search_downloads(self, query):
        """Search downloads by title or URL"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_pattern = f'%{query}%'
            cursor.execute('''
                SELECT * FROM downloads 
                WHERE title LIKE ? OR url LIKE ?
                ORDER BY downloaded_date DESC
            ''', (search_pattern, search_pattern))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def delete_download(self, download_id):
        """Delete a download from history"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM downloads WHERE id = ?', (download_id,))
                cursor.execute('DELETE FROM queue WHERE download_id = ?', (download_id,))
                conn.commit()
    
    def clear_history(self, older_than_days=None):
        """Clear download history, optionally only entries older than X days"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if older_than_days:
                    cursor.execute('''
                        DELETE FROM downloads 
                        WHERE datetime(downloaded_date) < datetime('now', ? || ' days')
                    ''', (-older_than_days,))
                else:
                    cursor.execute('DELETE FROM downloads')
                
                conn.commit()
    
    def get_statistics(self):
        """Get download statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total downloads
            cursor.execute('SELECT COUNT(*) FROM downloads')
            total = cursor.fetchone()[0]
            
            # Completed downloads
            cursor.execute("SELECT COUNT(*) FROM downloads WHERE status = 'completed'")
            completed = cursor.fetchone()[0]
            
            # Failed downloads
            cursor.execute("SELECT COUNT(*) FROM downloads WHERE status = 'failed'")
            failed = cursor.fetchone()[0]
            
            # Total file size
            cursor.execute('SELECT SUM(file_size) FROM downloads WHERE file_size IS NOT NULL')
            total_size = cursor.fetchone()[0] or 0
            
            # Downloads by format
            cursor.execute('''
                SELECT format_type, COUNT(*) 
                FROM downloads 
                GROUP BY format_type
            ''')
            by_format = dict(cursor.fetchall())
            
            return {
                'total_downloads': total,
                'completed': completed,
                'failed': failed,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'by_format': by_format
            }
    
    # Queue Management Methods
    
    def add_to_queue(self, download_id, priority=0):
        """Add a download to the queue"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO queue (download_id, priority, status)
                    VALUES (?, ?, 'queued')
                ''', (download_id, priority))
                
                conn.commit()
                return cursor.lastrowid
    
    def get_queue(self):
        """Get all queued downloads ordered by priority"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT q.*, d.* 
                FROM queue q
                JOIN downloads d ON q.download_id = d.id
                WHERE q.status IN ('queued', 'processing')
                ORDER BY q.priority DESC, q.added_date ASC
            ''')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def update_queue_status(self, queue_id, status):
        """Update queue item status"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                timestamp_field = None
                if status == 'processing':
                    timestamp_field = 'started_date'
                elif status == 'completed':
                    timestamp_field = 'completed_date'
                
                if timestamp_field:
                    cursor.execute(f'''
                        UPDATE queue 
                        SET status = ?, {timestamp_field} = ?
                        WHERE id = ?
                    ''', (status, datetime.now().isoformat(), queue_id))
                else:
                    cursor.execute('UPDATE queue SET status = ? WHERE id = ?', 
                                 (status, queue_id))
                
                conn.commit()
    
    def remove_from_queue(self, queue_id):
        """Remove item from queue"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM queue WHERE id = ?', (queue_id,))
                conn.commit()
    
    def get_next_queued_download(self):
        """Get the next download from queue"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT q.id as queue_id, q.*, d.*
                FROM queue q
                JOIN downloads d ON q.download_id = d.id
                WHERE q.status = 'queued'
                ORDER BY q.priority DESC, q.added_date ASC
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            return dict(row) if row else None

