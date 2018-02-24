import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule, MatToolbarModule } from '@angular/material';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatGridListModule } from '@angular/material/grid-list';

@NgModule({
  imports: [ MatButtonModule, MatToolbarModule, MatSidenavModule, MatGridListModule ],
  exports: [ MatButtonModule, MatToolbarModule, MatSidenavModule, MatGridListModule ],
})
export class MaterialModule { }