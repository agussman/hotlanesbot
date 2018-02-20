import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule, MatToolbarModule } from '@angular/material';
import { MatSidenavModule } from '@angular/material/sidenav';

@NgModule({
  imports: [MatButtonModule, MatToolbarModule, MatSidenavModule],
  exports: [MatButtonModule, MatToolbarModule, MatSidenavModule],
})
export class MaterialModule { }