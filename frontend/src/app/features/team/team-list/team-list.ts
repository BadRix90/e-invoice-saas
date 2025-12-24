import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService, User } from '../../../core/services/api';
import { AuthService } from '../../../core/services/auth';

@Component({
  selector: 'app-team-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatTableModule,
    MatDialogModule,
    MatSnackBarModule
  ],
  templateUrl: './team-list.html',
  styleUrl: './team-list.scss'
})
export class TeamListComponent implements OnInit {
  team = signal<User[]>([]);
  displayedColumns = ['username', 'email', 'name', 'role', 'date_joined'];
  isOwner = signal(false);

  constructor(
    private api: ApiService,
    private auth: AuthService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit() {
    this.loadTeam();
    this.checkOwner();
  }

  loadTeam() {
    this.api.getTeam().subscribe({
      next: (users) => this.team.set(users),
      error: () => this.snackBar.open('Fehler beim Laden der Team-Mitglieder', 'OK', { duration: 3000 })
    });
  }

  checkOwner() {
    const user = this.auth.currentUser();
    this.isOwner.set(user?.role === 'owner');
  }

  openAddDialog() {
    // TODO: Dialog implementieren (nächster Schritt)
    this.snackBar.open('Dialog kommt im nächsten Schritt', 'OK', { duration: 2000 });
  }
}
