import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, interval } from 'rxjs';
import { switchMap, catchError, of } from 'rxjs';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

export interface QueryResponse {
  success: boolean;
  query?: string;
  result?: string;
  error?: string;
  routing?: {
    handler: string;
    confidence: number;
  };
}

export interface HealthResponse {
  status: string;
  crew: string;
  rag_pipeline: string;
  qdrant?: {
    status: string;
    vectors?: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = 'http://localhost:8003';
  public messages: Message[] = [];

  constructor(private http: HttpClient) {}

  sendQuery(query: string): Observable<QueryResponse> {
    return this.http.post<QueryResponse>(`${this.apiUrl}/query`, { query });
  }

  checkHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.apiUrl}/health`).pipe(
      catchError(() => of({ 
        status: 'error', 
        crew: 'not initialized', 
        rag_pipeline: 'not initialized' 
      }))
    );
  }

  startHealthCheck(): Observable<HealthResponse> {
    return interval(10000).pipe(
      switchMap(() => this.checkHealth())
    );
  }

  addMessage(message: Message): void {
    this.messages.push({
      ...message,
      timestamp: new Date()
    });
  }

  clearMessages(): void {
    this.messages = [];
  }
}