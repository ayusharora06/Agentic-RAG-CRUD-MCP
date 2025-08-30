import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ChatService, Message, HealthResponse } from './services/chat.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'AI Agent Chat';
  inputMessage = '';
  isLoading = false;
  backendStatus: 'online' | 'offline' = 'offline';
  healthSubscription?: Subscription;

  constructor(public chatService: ChatService) {}

  ngOnInit(): void {
    // Initial health check
    this.checkHealth();
    
    // Start periodic health check
    this.healthSubscription = this.chatService.startHealthCheck().subscribe(
      (health: HealthResponse) => {
        this.backendStatus = health.status === 'healthy' ? 'online' : 'offline';
      }
    );
  }

  ngOnDestroy(): void {
    if (this.healthSubscription) {
      this.healthSubscription.unsubscribe();
    }
  }

  checkHealth(): void {
    this.chatService.checkHealth().subscribe(
      (health: HealthResponse) => {
        this.backendStatus = health.status === 'healthy' ? 'online' : 'offline';
      }
    );
  }

  sendMessage(): void {
    if (!this.inputMessage.trim()) {
      return;
    }

    const userMessage = this.inputMessage;
    this.inputMessage = '';
    this.isLoading = true;

    // Add user message
    this.chatService.addMessage({
      role: 'user',
      content: userMessage
    });

    // Send query to backend
    this.chatService.sendQuery(userMessage).subscribe({
      next: (response) => {
        this.isLoading = false;
        
        if (response.success && response.result) {
          // Add assistant response
          this.chatService.addMessage({
            role: 'assistant',
            content: response.result
          });
        } else {
          // Add error message
          this.chatService.addMessage({
            role: 'assistant',
            content: `❌ Error: ${response.error || 'No response generated'}`
          });
        }
      },
      error: (error) => {
        this.isLoading = false;
        this.chatService.addMessage({
          role: 'assistant',
          content: `❌ Error: ${error.message || 'Failed to connect to backend'}`
        });
      }
    });
  }

  clearChat(): void {
    this.chatService.clearMessages();
  }

  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }
}